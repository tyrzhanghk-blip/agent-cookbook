# 案例6：handoff

## 学什么
- `Agent(handoffs=[agent_a, agent_b])`：给 Agent 一组可以"转交"的对象。
- 和案例5的 `as_tool` 关键区别：
  - `as_tool`：调度者调用专家，**拿到结果后自己还在场**，可以继续加工、汇总。
  - `handoff`：触发后**控制权整个转移**给专科 Agent，原 Agent 不再参与这轮对话。
- `result.last_agent`：告诉你这一轮对话最终是哪个 Agent 收尾的，验证 handoff 是否真的发生了。

## 怎么运行
```bash
uv run python cases/case6_handoff/main.py
```

## 预期输出
账单问题最终由 `BillingAgent` 收尾，技术问题由 `TechSupportAgent` 收尾。

## 下一步
案例7讲安全护栏（guardrails）：怎么在交给模型之前/之后做校验。
