# lazyeval

`lazyeval` 是一个纯标准库的**惰性表达式求值**库。

- 语言 / 运行：Python 3，只用标准库（`unittest` 跑用例），无第三方依赖。
- 自检：`scripts/check.sh`（内部调用 `check/check.py`，那是固定验收程序，**别改**）。
- 目录：

  ```
  lazyeval/__init__.py   包出口
  lazyeval/nodes.py      AST 数据定义 + 解析器 —— 完整实现
  lazyeval/effects.py    可观察的副作用计数器 —— 完整实现
  lazyeval/eval.py       求值器（唯一入口 eval(node, env, effects)）
  tests/test_eval.py     既有 15 个用例（纯表达式），当前全绿
  repro.py               调用方给的最小复现
  check/check.py         固定验收程序：10 个场景
  ```

## 对外契约（8 条）

1. `eval(node, env, effects)` 是**唯一**求值入口；`and` / `or` 必须**短路**：
   左侧已决定结果时右侧**不得求值**（副作用计数与异常都不得发生）。
2. 三元 `cond ? a : b` 只求值被选中的那一支。
3. `pipe(x, f, g)` 是顺序组合，求值顺序从左到右且**每个函数恰好一次**。
4. 求值过程中抛出的异常必须**原样传播**（类型与消息都不许换），
   不许被内部 `try/except` 吞掉后返回默认值。
5. `Effects` 的计数必须如实反映实际求值次数：短路掉的子树贡献 0，被求值的节点贡献 1。
6. 惰性序列（`RangeNode` / `MapNode`）物化一次后必须**记住**结果：
   同一个节点求值两次，副作用计数只增加第一次的量。
7. 同一个 AST 可以被 `eval` 多次（可重入），内部不得缓存跨调用的状态。
8. 结果不依赖 `dict` 迭代顺序；`env` 里同名变量以最后一次绑定为准。

## 自检

```
python3 -m unittest discover -s tests
python3 repro.py
python3 check/check.py          # 也支持 -list 与 --only <组>
```
