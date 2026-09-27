"""可观察的副作用计数器。

求值器每「实际求值」一个带名字的调用/惰性节点，就通过 :meth:`record` 记一笔。
外部只通过 :meth:`count` / :meth:`log` 观察，通过 :meth:`reset` 清零。
"""

__all__ = ["Effects"]


class Effects(object):
    """按名字累计副作用发生次数，并保留发生顺序。"""

    def __init__(self):
        self._counts = {}
        self._order = []

    def record(self, name):
        """登记一次名为 ``name`` 的副作用（由求值器调用）。"""
        self._counts[name] = self._counts.get(name, 0) + 1
        self._order.append(name)

    def count(self, name):
        """``name`` 累计发生的次数；从未发生返回 0。"""
        return self._counts.get(name, 0)

    def log(self):
        """按发生顺序返回全部副作用名字的副本。"""
        return list(self._order)

    def reset(self):
        """清空计数与顺序。"""
        self._counts.clear()
        del self._order[:]

    def __repr__(self):
        return "Effects(%r)" % (dict(self._counts),)
