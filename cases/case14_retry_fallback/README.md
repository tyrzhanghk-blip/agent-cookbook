# 案例14：重试与降级策略

## 学什么
- **自动重试**：`ModelSettings(retry=ModelRetrySettings(max_retries=N))`。
  单次模型调用失败（超时、5xx）时，SDK 在内部自动重试，不用你手写 `for i in range(3): try/except`。
  可以配合 `ModelRetryBackoffSettings` 配置重试间隔（避免立刻重打把网关打得更崩）。
- **手动降级（fallback）**：自动重试全部用完仍然失败后，代码层面 `try/except` 住异常，换一个更简单/更稳的模型再跑一次。
  这是"案例3踩的坑"（强模型在复杂任务上偶尔不稳定）的系统化解法：
  关键路径上永远要有一个"退路"，而不是指望单一模型/单一请求100%成功。
- 常见异常类型在 `agents.exceptions` 下（`ModelTimeoutError`、`AgentsException` 等），按需 catch。

## 怎么运行
```bash
uv run python cases/case14_retry_fallback/main.py
```

## 预期输出
- 第一部分：正常拿到回答（偶尔背后发生了自动重试，你看不到但生效了）。
- 第二部分：主模型给了很短的超时（故意设置成容易失败），失败后能看到"降级到备用模型"的日志，并最终拿到备用模型的回答。

## 下一步
案例15讲怎么给 Agent 写回归测试，避免改 prompt 改出退化。
