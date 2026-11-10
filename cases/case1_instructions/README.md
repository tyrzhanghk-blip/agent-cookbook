# 案例1：指令（instructions）

## 学什么
- `instructions` 可以是静态字符串（案例0），也可以是一个**函数**：`(RunContextWrapper, Agent) -> str`。
- 用函数形式时，SDK 在每次运行时调用它，可以根据 `context`（运行时传入的任意业务对象）动态拼出不同的角色设定。
- `Agent[T]` 的类型参数 `T` 就是 `context` 的类型，配合 `RunContextWrapper[T]` 得到类型提示。

## 怎么运行
```bash
uv run python cases/case1_instructions/main.py
```

## 预期输出
同一个 Agent，面对 beginner 和 expert 两种 context，给出的讲解风格完全不同。

## 下一步
案例2会给 Agent 加上第一个工具（function_tool）。
