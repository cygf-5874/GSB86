客服转过来的原话：「不该算的那笔也被扣了」—— lazyeval 是 Python 3 的惰性求值库，
只用标准库（unittest 跑用例），没有第三方依赖，自检走 `scripts/check.sh`
（`check/` 是固定验收程序，别改）。

`nodes.py`、`effects.py` 是对的；问题在 `eval.py`。
`tests/test_eval.py` 的 15 个用例当前全绿，但它们都是没有副作用、也不会出错的纯表达式。
`repro.py` 是调用方给的最小输入。

任务：找出 `eval.py` 里违反 README「对外契约」的地方并修好，
既有用例保持全绿，固定件全过。

验收：
- python3 -m unittest discover -s tests 退出码 0；
- python3 repro.py 退出码 0（那两处说不通的地方不再复现）；
- python3 check/check.py 退出码 0，10 个场景全过（shortcircuit 3 + effects 3 + errors 2 + reentrant 2）。

约束：
1. 不改 `check/`、不改 `repro.py`、不改 `nodes.py`、不改 `effects.py`、不改 `tests/test_eval.py`。
2. 不引入第三方依赖，只用标准库。
3. 不许用 `time`、`random` 参与结果。
4. 公开的函数签名不变（可新增内部函数）。
