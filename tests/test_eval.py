"""lazyeval 的既有回归用例。

这些用例只覆盖**纯表达式**：不带副作用、不抛异常、结果也不依赖短路行为。
它们在初始仓库里全部通过。
"""

import unittest

from lazyeval import (
    BinOp,
    BoolOp,
    Const,
    Effects,
    IfExp,
    MapNode,
    Name,
    Pipe,
    RangeNode,
    eval as evaluate,
    parse,
)


def inc(value):
    return value + 1


def double(value):
    return value * 2


ENV = {
    "answer": 42,
    "greeting": "hi",
    "inc": inc,
    "double": double,
}


def run(node, env=None):
    effects = Effects()
    return evaluate(node, ENV if env is None else env, effects)


class ConstAndNameTests(unittest.TestCase):
    def test_const_int(self):
        self.assertEqual(7, run(Const(7)))

    def test_const_string(self):
        self.assertEqual("hi", run(Const("hi")))

    def test_name_lookup_returns_bound_value(self):
        self.assertEqual(42, run(Name("answer")))
        self.assertEqual("hi", run(Name("greeting")))


class ArithmeticTests(unittest.TestCase):
    def test_addition(self):
        self.assertEqual(5, run(BinOp("+", Const(2), Const(3))))

    def test_operator_precedence_via_parser(self):
        self.assertEqual(7, run(parse("1 + 2 * 3")))
        self.assertEqual(9, run(parse("(1 + 2) * 3")))

    def test_floordiv_mod_pow(self):
        self.assertEqual(3, run(BinOp("//", Const(7), Const(2))))
        self.assertEqual(1, run(BinOp("%", Const(7), Const(2))))
        self.assertEqual(8, run(BinOp("**", Const(2), Const(3))))

    def test_true_division_and_unary_minus(self):
        self.assertAlmostEqual(2.5, run(BinOp("/", Const(5), Const(2))))
        self.assertEqual(-4, run(BinOp("-", Const(0), Const(4))))


class LogicValueTests(unittest.TestCase):
    def test_and_returns_right_when_left_truthy(self):
        self.assertEqual(9, run(BoolOp("and", Const(1), Const(9))))

    def test_and_returns_left_when_left_falsy(self):
        self.assertEqual(0, run(BoolOp("and", Const(0), Const(9))))

    def test_or_returns_left_when_left_truthy(self):
        self.assertEqual(1, run(BoolOp("or", Const(1), Const(9))))

    def test_or_returns_right_when_left_falsy(self):
        self.assertEqual(9, run(BoolOp("or", Const(0), Const(9))))


class TernaryTests(unittest.TestCase):
    def test_ternary_true_branch_value(self):
        self.assertEqual(10, run(IfExp(Const(True), Const(10), Const(20))))
        self.assertEqual(10, run(parse("1 ? 10 : 20")))

    def test_ternary_false_branch_value(self):
        self.assertEqual(20, run(IfExp(Const(False), Const(10), Const(20))))


class PipeAndLazyTests(unittest.TestCase):
    def test_pipe_applies_left_to_right(self):
        self.assertEqual(8, run(parse("pipe(3, inc, double)")))
        self.assertEqual(7, run(parse("pipe(3, double, inc)")))

    def test_map_over_range_values(self):
        node = MapNode("inc", RangeNode(0, 4))
        self.assertEqual([1, 2, 3, 4], run(node))


if __name__ == "__main__":
    unittest.main()
