# 案例4：上下文与记忆

## 学什么
- `context`：你在 `Runner.run_sync(agent, input, context=...)` 传入的任意业务对象。
  - 模型**看不到**它，只有 `instructions` 函数（案例1）和工具（通过 `RunContextWrapper`，案例2/3）能读到。
  - 典型用途：用户身份、权限、数据库连接等不该暴露给模型的东西。
- 对话历史（"记忆"）：模型是**无状态**的，想让它记住上一轮说的话，必须显式把历史传回去。
  - `result.to_input_list()` 能拿到"这一轮完整的输入+输出"，拼到下一轮的 input 里即可实现多轮对话。
  - 不这样做的话，每次 `Runner.run_sync` 都是全新的、无记忆的对话。
- 这两者不要混淆：**context 是开发者的状态，对话历史是模型的状态**。

## 怎么运行
```bash
uv run python cases/case4_context_memory/main.py
```

## 预期输出
- context 演示：VIP 用户拿到"9折"。
- 记忆演示：第二轮能正确说出"小明"，因为历史被带过去了。

## 下一步
案例5讲多专家协作：把一个 Agent 当作另一个 Agent 的工具（as_tool）。
