# 案例12：人工审批（human-in-the-loop）

## 学什么
- `@function_tool(needs_approval=True)`：把一个工具标记为"调用前必须经人工批准"。
  `needs_approval` 也可以传一个函数（`(context, args, call_id) -> bool`），实现"只有金额超过阈值才需要审批"这种动态规则。
- `result.interruptions`：运行遇到需要审批的工具调用时会在这里"暂停"，不会真的执行，而是把待审批项列出来。
- `result.to_state()` / `state.approve(item)` / `state.reject(item)`：决策之后，把决定写回运行状态。
- `Runner.run_sync(agent, state)`：把带着审批决定的 state 传回去，继续跑完这次对话——
  被批准的工具调用这时才真正执行；被拒绝的，Agent 会知道"这个操作没通过"，需要自己决定怎么回应用户。
- 这个 state 是可以序列化的（`to_json`/`from_json`），意味着审批流程可以是**异步**的——
  先把 state 存到数据库，等人在另一个系统里点了"同意"按钮，再从数据库读出来恢复执行。

## 怎么运行
```bash
uv run python cases/case12_human_approval/main.py
```

## 预期输出
先打印"待审批"的工具调用（退款50元），再打印"审批通过"，最后打印退款真正执行后的结果。

## 下一步
案例16：把前面所有能力整合进一个带界面的真实产品（Web 或 CLI）。
