# 案例5：多专家 as_tool

## 学什么
- `agent.as_tool(tool_name=..., tool_description=...)`：把一个完整的 Agent 包装成另一个 Agent 能调用的"工具"。
- 调度者（这里是 `Concierge`）不关心专家内部怎么工作，只知道"调这个工具能拿到翻译结果"。
- 和案例6的 handoff 的区别：as_tool 之后，控制权**还在调度者手里**——调度者拿到专家的结果后，还能继续处理、汇总、追问；
  handoff 则是把整个对话的控制权**转移**给另一个 Agent（下一个案例讲）。

## 怎么运行
```bash
uv run python cases/case5_agents_as_tools/main.py
```

## 预期输出
Concierge 根据请求调用对应的翻译专家工具，并把结果呈现给用户。

## 下一步
案例6讲 handoff：把对话完全交接给另一个 Agent。
