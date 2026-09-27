#!/usr/bin/env python3
"""lazyeval 的固定验收程序。

场景（10 个）：shortcircuit 3 + effects 3 + errors 2 + reentrant 2。

本文件属于固定判据，解题方不得修改。所有判据都是确定性的：
不使用 ``random``、不使用 ``time``、不依赖 ``dict`` 迭代顺序。
"""

import argparse
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from lazyeval import (  # noqa: E402
    BinOp,
    BoolOp,
    Call,
    Const,
    Effects,
    IfExp,
    MapNode,
    RangeNode,
)
from lazyeval import eval as evaluate  # noqa: E402


def _verdict(ok, expected, actual):
    return (bool(ok), expected, actual)


def _call_totals(effects, names):
    return tuple(effects.count(name) for name in names)


# --------------------------------------------------------------------------
# shortcircuit 组：已决定结果的那一侧不得求值
# --------------------------------------------------------------------------

def scenario_shortcircuit_and_right_not_evaluated():
    def boom():
        raise RuntimeError("右侧不应被求值")

    effects = Effects()
    try:
        got = evaluate(BoolOp("and", Const(0), Call("boom")), {"boom": boom}, effects)
    except Exception as exc:  # noqa: BLE001
        return _verdict(False, "结果=0 且 boom 计数=0",
                        "%s: %s" % (type(exc).__name__, exc))
    ok = got == 0 and effects.count("boom") == 0
    return _verdict(ok, "结果=0 且 boom 计数=0",
                    "结果=%r boom 计数=%d" % (got, effects.count("boom")))


def scenario_shortcircuit_or_right_not_evaluated():
    def boom():
        raise RuntimeError("右侧不应被求值")

    effects = Effects()
    try:
        got = evaluate(BoolOp("or", Const(1), Call("boom")), {"boom": boom}, effects)
    except Exception as exc:  # noqa: BLE001
        return _verdict(False, "结果=1 且 boom 计数=0",
                        "%s: %s" % (type(exc).__name__, exc))
    ok = got == 1 and effects.count("boom") == 0
    return _verdict(ok, "结果=1 且 boom 计数=0",
                    "结果=%r boom 计数=%d" % (got, effects.count("boom")))


def scenario_shortcircuit_ternary_other_branch_not_evaluated():
    def boom():
        raise RuntimeError("未被选中那一支不应被求值")

    effects = Effects()
    node = IfExp(Const(True), Const(7), Call("boom"))
    try:
        got = evaluate(node, {"boom": boom}, effects)
    except Exception as exc:  # noqa: BLE001
        return _verdict(False, "结果=7 且 boom 计数=0",
                        "%s: %s" % (type(exc).__name__, exc))
    ok = got == 7 and effects.count("boom") == 0
    return _verdict(ok, "结果=7 且 boom 计数=0",
                    "结果=%r boom 计数=%d" % (got, effects.count("boom")))


# --------------------------------------------------------------------------
# effects 组：计数必须与真实求值次数一致
# --------------------------------------------------------------------------

def scenario_effects_count_matches_evaluation():
    def f():
        return 11

    effects = Effects()
    node = BoolOp("or", Const(0), Call("f"))
    try:
        got = evaluate(node, {"f": f}, effects)
    except Exception as exc:  # noqa: BLE001
        return _verdict(False, "结果=11 且 f 计数=1",
                        "%s: %s" % (type(exc).__name__, exc))
    ok = got == 11 and effects.count("f") == 1
    return _verdict(ok, "结果=11 且 f 计数=1",
                    "结果=%r f 计数=%d" % (got, effects.count("f")))


def scenario_effects_shortcircuited_subtree_contributes_zero():
    def f():
        return 11

    effects = Effects()
    node = BoolOp("and", Const(0), Call("f"))
    try:
        got = evaluate(node, {"f": f}, effects)
    except Exception as exc:  # noqa: BLE001
        return _verdict(False, "结果=0 且 f 计数=0",
                        "%s: %s" % (type(exc).__name__, exc))
    ok = got == 0 and effects.count("f") == 0
    return _verdict(ok, "结果=0 且 f 计数=0",
                    "结果=%r f 计数=%d" % (got, effects.count("f")))


def scenario_effects_lazy_sequence_materialized_once():
    def inc(value):
        return value + 1

    lazy = MapNode("inc", RangeNode(0, 3))
    node = Call("pair", (lazy, lazy))
    effects = Effects()
    env = {"inc": inc, "pair": lambda a, b: (a, b)}
    try:
        got = evaluate(node, env, effects)
    except Exception as exc:  # noqa: BLE001
        return _verdict(False, "结果=([1, 2, 3], [1, 2, 3]) 且 inc=3 map=1 range=1",
                        "%s: %s" % (type(exc).__name__, exc))
    counts = _call_totals(effects, ("inc", "map", "range"))
    ok = got == ([1, 2, 3], [1, 2, 3]) and counts == (3, 1, 1)
    return _verdict(ok, "结果=([1, 2, 3], [1, 2, 3]) 且 inc=3 map=1 range=1",
                    "结果=%r 且 inc=%d map=%d range=%d" % (got, counts[0], counts[1], counts[2]))


# --------------------------------------------------------------------------
# errors 组：异常必须原样传播
# --------------------------------------------------------------------------

def scenario_errors_zero_division_propagates():
    effects = Effects()
    try:
        got = evaluate(BinOp("/", Const(1), Const(0)), {}, effects)
    except ZeroDivisionError:
        return _verdict(True, "抛 ZeroDivisionError", "抛 ZeroDivisionError")
    except Exception as exc:  # noqa: BLE001
        return _verdict(False, "抛 ZeroDivisionError", "%s: %s" % (type(exc).__name__, exc))
    return _verdict(False, "抛 ZeroDivisionError", "返回 %r" % (got,))


def scenario_errors_exception_propagates_unchanged():
    def boom():
        raise ValueError("kaboom")

    effects = Effects()
    node = BinOp("+", Call("boom"), Const(1))
    try:
        got = evaluate(node, {"boom": boom}, effects)
    except ValueError as exc:
        ok = str(exc) == "kaboom"
        return _verdict(ok, "ValueError('kaboom')", "ValueError(%r)" % (str(exc),))
    except Exception as exc:  # noqa: BLE001
        return _verdict(False, "ValueError('kaboom')", "%s: %s" % (type(exc).__name__, exc))
    return _verdict(False, "ValueError('kaboom')", "返回 %r" % (got,))


# --------------------------------------------------------------------------
# reentrant 组：同一个 AST 可以被求值多次，且不留跨调用状态
# --------------------------------------------------------------------------

def _reentrant_node():
    def inc(value):
        return value + 1

    lazy = MapNode("inc", RangeNode(0, 4))
    node = Call("pair", (lazy, lazy))
    env = {"inc": inc, "pair": lambda a, b: (a, b)}
    return node, env


def scenario_reentrant_same_ast_same_result():
    node, env = _reentrant_node()
    first = evaluate(node, env, Effects())
    second = evaluate(node, env, Effects())
    ok = first == second == ([1, 2, 3, 4], [1, 2, 3, 4])
    return _verdict(ok, "两次结果均为 ([1, 2, 3, 4], [1, 2, 3, 4])",
                    "%r / %r" % (first, second))


def scenario_reentrant_no_cross_call_state():
    node, env = _reentrant_node()
    names = ("inc", "map", "range", "pair")
    snapshots = []
    for _ in range(2):
        effects = Effects()
        evaluate(node, env, effects)
        snapshots.append(_call_totals(effects, names))
    ok = snapshots[0] == snapshots[1]
    return _verdict(ok, "两次调用的计数相同",
                    "%r / %r" % (snapshots[0], snapshots[1]))


SCENARIOS = (
    ("shortcircuit", "and-right-not-evaluated", scenario_shortcircuit_and_right_not_evaluated),
    ("shortcircuit", "or-right-not-evaluated", scenario_shortcircuit_or_right_not_evaluated),
    ("shortcircuit", "ternary-other-branch-not-evaluated",
     scenario_shortcircuit_ternary_other_branch_not_evaluated),
    ("effects", "count-matches-evaluation", scenario_effects_count_matches_evaluation),
    ("effects", "shortcircuited-subtree-contributes-zero",
     scenario_effects_shortcircuited_subtree_contributes_zero),
    ("effects", "lazy-sequence-materialized-once",
     scenario_effects_lazy_sequence_materialized_once),
    ("errors", "zero-division-propagates", scenario_errors_zero_division_propagates),
    ("errors", "exception-propagates-unchanged",
     scenario_errors_exception_propagates_unchanged),
    ("reentrant", "same-ast-same-result", scenario_reentrant_same_ast_same_result),
    ("reentrant", "no-cross-call-state", scenario_reentrant_no_cross_call_state),
)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="check.py")
    parser.add_argument("-list", dest="list_scenarios", action="store_true",
                        help="列出全部场景后退出")
    parser.add_argument("--only", dest="only", default=None,
                        help="只运行指定组")
    args = parser.parse_args(argv)

    if args.list_scenarios:
        for group, name, _func in SCENARIOS:
            print("%s/%s" % (group, name))
        return 0

    selected = [s for s in SCENARIOS if args.only is None or s[0] == args.only]
    passed = 0
    for group, name, func in selected:
        try:
            ok, expected, actual = func()
        except Exception as exc:  # noqa: BLE001
            ok, expected, actual = False, "无异常", "%s: %s" % (type(exc).__name__, exc)
        if ok:
            passed += 1
            print("PASS %s/%s" % (group, name))
        else:
            print("FAIL %s/%s  期望=%s 实际=%s" % (group, name, expected, actual))

    print("结果：通过 %d/%d" % (passed, len(selected)))
    return 0 if selected and passed == len(selected) else 1


if __name__ == "__main__":
    sys.exit(main())
