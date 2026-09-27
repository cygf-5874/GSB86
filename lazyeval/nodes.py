"""AST 数据定义与解析器。

本模块只负责把源码文本解析成 AST 节点对象，不做任何求值。
节点之间按**对象身份**区分（`eq=False`），因此两个结构相同的节点是两个
不同的对象；求值器可以据此把「同一个节点」与「两个等价的节点」分开。
"""

import re

__all__ = [
    "Node",
    "Const",
    "Name",
    "BinOp",
    "BoolOp",
    "IfExp",
    "Call",
    "Pipe",
    "RangeNode",
    "MapNode",
    "parse",
]


class Node(object):
    """AST 节点基类。"""

    __slots__ = ()


class Const(Node):
    """字面量。"""

    __slots__ = ("value",)

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return "Const(%r)" % (self.value,)


class Name(Node):
    """变量引用；求值时在 env 中查名。"""

    __slots__ = ("name",)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "Name(%r)" % (self.name,)


class BinOp(Node):
    """二元算术运算：op ∈ {+ - * / // % **}。"""

    __slots__ = ("op", "left", "right")

    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return "BinOp(%r, %r, %r)" % (self.op, self.left, self.right)


class BoolOp(Node):
    """逻辑运算：op ∈ {and, or}，左右各一个操作数。"""

    __slots__ = ("op", "left", "right")

    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return "BoolOp(%r, %r, %r)" % (self.op, self.left, self.right)


class IfExp(Node):
    """三元表达式 ``cond ? body : orelse``。"""

    __slots__ = ("cond", "body", "orelse")

    def __init__(self, cond, body, orelse):
        self.cond = cond
        self.body = body
        self.orelse = orelse

    def __repr__(self):
        return "IfExp(%r, %r, %r)" % (self.cond, self.body, self.orelse)


class Call(Node):
    """按名字调用：``name(arg, ...)``。被调函数由 env 提供。"""

    __slots__ = ("name", "args")

    def __init__(self, name, args=()):
        self.name = name
        self.args = tuple(args)

    def __repr__(self):
        return "Call(%r, %r)" % (self.name, self.args)


class Pipe(Node):
    """顺序组合：``pipe(value, f, g, ...)``，从左到右逐个套用。"""

    __slots__ = ("value", "funcs")

    def __init__(self, value, funcs=()):
        self.value = value
        self.funcs = tuple(funcs)

    def __repr__(self):
        return "Pipe(%r, %r)" % (self.value, self.funcs)


class RangeNode(Node):
    """惰性整数序列：``range(start, stop)``。"""

    __slots__ = ("start", "stop")

    def __init__(self, start, stop):
        self.start = int(start)
        self.stop = int(stop)

    def __repr__(self):
        return "RangeNode(%r, %r)" % (self.start, self.stop)


class MapNode(Node):
    """惰性映射：``map(name, source)``，对 source 的每个元素套用 name。"""

    __slots__ = ("name", "source")

    def __init__(self, name, source):
        self.name = name
        self.source = source

    def __repr__(self):
        return "MapNode(%r, %r)" % (self.name, self.source)


# ---------------------------------------------------------------------------
# 解析器：把源码文本解析成 AST
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(
    r"(?P<num>\d+\.\d+|\d+)"
    r"|(?P<str>'[^']*'|\"[^\"]*\")"
    r"|(?P<op>\*\*|//|[-+*/%(),?:])"
    r"|(?P<name>[A-Za-z_][A-Za-z0-9_]*)"
)

_KEYWORDS = {
    "and": ("kw", "and"),
    "or": ("kw", "or"),
    "True": ("const", True),
    "False": ("const", False),
    "None": ("const", None),
}

_KNOWN_CALLS = ("range", "map", "pipe")


def _tokenize(text):
    tokens = []
    pos = 0
    size = len(text)
    while pos < size:
        if text[pos].isspace():
            pos += 1
            continue
        match = _TOKEN_RE.match(text, pos)
        if match is None:
            raise SyntaxError("无法识别的位置 %d: %r" % (pos, text[pos:pos + 8]))
        kind = match.lastgroup
        raw = match.group()
        pos = match.end()
        if kind == "num":
            tokens.append(("num", float(raw) if "." in raw else int(raw)))
        elif kind == "str":
            tokens.append(("str", raw[1:-1]))
        elif kind == "op":
            tokens.append(("op", raw))
        else:
            special = _KEYWORDS.get(raw)
            tokens.append(special if special is not None else ("name", raw))
    tokens.append(("end", None))
    return tokens


class _Parser(object):
    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0

    # -- 辅助 ------------------------------------------------------------
    def _peek(self):
        return self.tokens[self.index]

    def _advance(self):
        token = self.tokens[self.index]
        self.index += 1
        return token

    def _accept(self, kind, value=None):
        token = self.tokens[self.index]
        if token[0] == kind and (value is None or token[1] == value):
            self.index += 1
            return token
        return None

    def _expect(self, kind, value=None):
        token = self._accept(kind, value)
        if token is None:
            got = self.tokens[self.index]
            raise SyntaxError("期望 %r，实际 %r" % ((kind, value), got))
        return token

    # -- 文法 ------------------------------------------------------------
    def parse_expr(self):
        node = self.parse_or()
        if self._accept("op", "?"):
            body = self.parse_expr()
            self._expect("op", ":")
            orelse = self.parse_expr()
            node = IfExp(node, body, orelse)
        return node

    def parse_or(self):
        node = self.parse_and()
        while self._accept("kw", "or"):
            node = BoolOp("or", node, self.parse_and())
        return node

    def parse_and(self):
        node = self.parse_sum()
        while self._accept("kw", "and"):
            node = BoolOp("and", node, self.parse_sum())
        return node

    def parse_sum(self):
        node = self.parse_term()
        while True:
            if self._accept("op", "+"):
                node = BinOp("+", node, self.parse_term())
            elif self._accept("op", "-"):
                node = BinOp("-", node, self.parse_term())
            else:
                return node

    def parse_term(self):
        node = self.parse_power()
        while True:
            if self._accept("op", "*"):
                node = BinOp("*", node, self.parse_power())
            elif self._accept("op", "//"):
                node = BinOp("//", node, self.parse_power())
            elif self._accept("op", "/"):
                node = BinOp("/", node, self.parse_power())
            elif self._accept("op", "%"):
                node = BinOp("%", node, self.parse_power())
            else:
                return node

    def parse_power(self):
        node = self.parse_unary()
        if self._accept("op", "**"):
            node = BinOp("**", node, self.parse_power())
        return node

    def parse_unary(self):
        if self._accept("op", "-"):
            return BinOp("-", Const(0), self.parse_unary())
        return self.parse_primary()

    def parse_primary(self):
        token = self._peek()
        if token[0] == "num" or token[0] == "str" or token[0] == "const":
            self._advance()
            return Const(token[1])
        if token[0] == "op" and token[1] == "(":
            self._advance()
            node = self.parse_expr()
            self._expect("op", ")")
            return node
        if token[0] == "name":
            self._advance()
            name = token[1]
            if self._accept("op", "("):
                args = self.parse_args()
                return self.build_call(name, args)
            return Name(name)
        raise SyntaxError("无法解析的记号 %r" % (token,))

    def parse_args(self):
        args = []
        if self._accept("op", ")"):
            return args
        args.append(self.parse_expr())
        while self._accept("op", ","):
            if self._accept("op", ")"):
                return args
            args.append(self.parse_expr())
        self._expect("op", ")")
        return args

    def build_call(self, name, args):
        if name == "range":
            if len(args) != 2 or not all(isinstance(a, Const) for a in args):
                raise SyntaxError("range(start, stop) 需要两个字面量整数")
            return RangeNode(args[0].value, args[1].value)
        if name == "map":
            if len(args) != 2 or not isinstance(args[0], Name):
                raise SyntaxError("map(name, source) 的第一个参数必须是函数名")
            return MapNode(args[0].name, args[1])
        if name == "pipe":
            if not args or not all(isinstance(a, Name) for a in args[1:]):
                raise SyntaxError("pipe(value, f, g, ...) 的后续参数必须是函数名")
            return Pipe(args[0], [a.name for a in args[1:]])
        return Call(name, args)


def parse(text):
    """把表达式文本解析成 AST。"""
    parser = _Parser(_tokenize(text))
    node = parser.parse_expr()
    tail = parser._peek()
    if tail[0] != "end":
        raise SyntaxError("表达式结束后还有多余记号 %r" % (tail,))
    return node
