"""lazyeval：纯标准库的惰性表达式求值库。

对外出口：

- :func:`eval`        唯一求值入口 ``eval(node, env, effects)``
- :class:`Effects`    可观察的副作用计数器
- 节点类型            ``Const`` / ``Name`` / ``BinOp`` / ``BoolOp`` /
                      ``IfExp`` / ``Call`` / ``Pipe`` / ``RangeNode`` / ``MapNode``
- :func:`parse`       把表达式文本解析成 AST
"""

from .effects import Effects
from .eval import eval
from .nodes import (
    BinOp,
    BoolOp,
    Call,
    Const,
    IfExp,
    MapNode,
    Name,
    Node,
    Pipe,
    RangeNode,
    parse,
)

__all__ = [
    "eval",
    "parse",
    "Effects",
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
]
