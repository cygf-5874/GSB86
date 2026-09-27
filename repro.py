#!/usr/bin/env python3
"""调用方给的最小复现。

两处说不通的地方：一次计数对不上，一次本该报错却拿到了一个值。
修好之后本脚本应当静默退出 0。
"""

import sys

from lazyeval import BinOp, BoolOp, Call, Const, Effects
from lazyeval import eval as evaluate


def charge():
    return 5


def main():
    broken = []

    effects = Effects()
    value = evaluate(BoolOp("or", Const(0), Call("charge")), {"charge": charge}, effects)
    counted = effects.count("charge")
    if (value, counted) != (5, 1):
        print("副作用计数 %d 次，期望 1 次" % (counted,))
        broken.append("effects")

    effects = Effects()
    try:
        value = evaluate(BinOp("/", Const(1), Const(0)), {}, effects)
    except ZeroDivisionError:
        pass
    else:
        print("本该抛 ZeroDivisionError 却拿到 %s" % (value,))
        broken.append("error")

    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
