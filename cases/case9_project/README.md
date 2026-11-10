# 案例9：真实小产品 —— 订单客服工作台

## 整合了什么
一个支持多轮对话的电商客服 Agent，融合了前面所有案例的能力：

| 能力 | 对应案例 | 在这里的用法 |
|---|---|---|
| 工具 | 案例2/3 | `lookup_order` / `lookup_tracking` 查订单和物流 |
| context | 案例4 | `CurrentUser`（身份信息），`greet_user` 工具能读到，模型本身看不到 |
| 对话记忆 | 案例4 | `chat()` 函数用 `result.to_input_list()` 把历史带入下一轮 |
| as_tool | 案例5 | `faq_agent` 作为 `ask_faq` 工具，被主客服按需调用 |
| handoff | 案例6 | 用户明确要退款时，转交给 `RefundAgent` |
| guardrail | 案例7 | 拦截和电商客服完全无关的请求（比如让它写诗） |
| tracing | 案例8 | 自定义处理器，打印每次工具调用/handoff，而不依赖官方上报后端 |

## 怎么运行
```bash
uv run python cases/case9_project/main.py
```

## 预期输出
依次演示：查订单 → 追问物流（靠记忆知道问的是哪个订单）→ 查 FAQ → 申请退款触发 handoff → 写诗请求被护栏拦截。
每一步工具调用/handoff 都会在前面打印一行 `[调用工具]` 或 `[handoff]` 日志。

## 这一路学到了什么
从案例0的最小闭环，到这里一个结构完整的客服 Agent——核心思路始终是：
**给 Agent 恰到好处的工具、恰到好处的角色设定，组合出复杂行为**，而不是用一个巨大的 prompt 硬撑所有逻辑。
