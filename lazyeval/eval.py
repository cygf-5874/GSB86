"""表达式求值器。

对外只有一个入口 :func:`eval`：``eval(node, env, effects)``。

- ``node``    由 :mod:`lazyeval.nodes` 提供的 AST；
- ``env``     名字到值 / 可调用对象的映射；
- ``effects``  :class:`lazyeval.effects.Effects` 实例，用来观察副作用。

求值规则见 README 的「对外契约」。
"""

import operator

from .nodes import (
    BinOp,
    BoolOp,
    Call,
    Const,
    IfExp,
    MapNode,
    Name,
    Pipe,
    RangeNode,
)

__all__ = ["eval"]

_OPS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "//": operator.floordiv,
    "%": operator.mod,
    "**": operator.pow,
}


def _truthy(value):
    return bool(value)


class _Evaluator(object):
    def __init__(self, env, effects):
        self.env = env
        self.effects = effects

    # -- 调度 ------------------------------------------------------------
    def evaluate(self, node):
        if isinstance(node, Const):
            return node.value
        if isinstance(node, Name):
            return self._name(node)
        if isinstance(node, BinOp):
            return self._binop(node)
        if isinstance(node, BoolOp):
            return self._boolop(node)
        if isinstance(node, IfExp):
            return self._ifexp(node)
        if isinstance(node, Call):
            return self._call(node)
        if isinstance(node, Pipe):
            return self._pipe(node)
        if isinstance(node, RangeNode):
            return self._range(node)
        if isinstance(node, MapNode):
            return self._map(node)
        raise TypeError("不支持的节点类型：%s" % (type(node).__name__,))

    # -- 各节点 ----------------------------------------------------------
    def _name(self, node):
        if node.name not in self.env:
            raise NameError("未绑定的名字：%r" % (node.name,))
        return self.env[node.name]

    def _binop(self, node):
        try:
            left = self.evaluate(node.left)
            right = self.evaluate(node.right)
            return _OPS[node.op](left, right)
        except Exception:
            return None

    def _boolop(self, node):
        left = self.evaluate(node.left)
        self._note_effects(node.right)
        right = self.evaluate(node.right)
        if node.op == "and":
            return right if _truthy(left) else left
        if node.op == "or":
            return left if _truthy(left) else right
        raise ValueError("未知逻辑运算符：%r" % (node.op,))

    def _ifexp(self, node):
        cond = _truthy(self.evaluate(node.cond))
        body = self.evaluate(node.body)
        orelse = self.evaluate(node.orelse)
        return body if cond else orelse

    def _call(self, node):
        args = [self.evaluate(arg) for arg in node.args]
        return self._apply(node.name, args)

    def _pipe(self, node):
        value = self.evaluate(node.value)
        for name in node.funcs:
            value = self._apply(name, (value,))
        return value

    # -- 惰性序列 --------------------------------------------------------
    def _range(self, node):
        self.effects.record("range")
        return list(range(node.start, node.stop))

    def _map(self, node):
        self.effects.record("map")
        source = self.evaluate(node.source)
        return [self._apply(node.name, (item,)) for item in source]

    # -- 调用 ------------------------------------------------------------
    def _apply(self, name, args):
        if name not in self.env:
            raise NameError("未绑定的可调用名：%r" % (name,))
        self.effects.record(name)
        return self.env[name](*args)

    def _note_effects(self, node):
        if isinstance(node, Call):
            self.effects.record(node.name)
        elif isinstance(node, RangeNode):
            self.effects.record("range")
        elif isinstance(node, MapNode):
            self.effects.record("map")
        for child in self._children(node):
            self._note_effects(child)

    @staticmethod
    def _children(node):
        if isinstance(node, BinOp):
            return (node.left, node.right)
        if isinstance(node, BoolOp):
            return (node.left, node.right)
        if isinstance(node, IfExp):
            return (node.cond, node.body, node.orelse)
        if isinstance(node, Call):
            return tuple(node.args)
        if isinstance(node, Pipe):
            return (node.value,)
        if isinstance(node, MapNode):
            return (node.source,)
        return ()


def eval(node, env, effects):
    """对 ``node`` 求值，``env`` 提供名字绑定，``effects`` 记录副作用。"""
    evaluator = _Evaluator(env, effects)
    return evaluator.evaluate(node)
