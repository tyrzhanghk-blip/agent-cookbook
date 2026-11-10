"""
案例12：人工审批（human-in-the-loop）
目标：有些工具调用风险太高（真实转账、删除数据、发送外部邮件……），不能让 Agent 自己说了算，
必须暂停下来，等人确认之后才真正执行。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import Agent, ModelSettings, Runner, function_tool
from common.env import default_model, load_env

load_env()


@function_tool
def check_order_status(order_id: str) -> str:
    """查询订单状态，低风险操作，不需要审批。"""
    return f"订单{order_id}状态：已完成"


@function_tool(needs_approval=True)  # 关键：标记为"需要人工审批"才能真正执行
def issue_refund(order_id: str, amount: float) -> str:
    """给指定订单执行退款，涉及真实资金变动，必须人工审批后才能执行。

    Args:
        order_id: 订单号。
        amount: 退款金额，单位元。
    """
    # 这里是退款"真正执行"的逻辑——只有通过审批后，Runner 才会真的跑到这一行。
    return f"已为订单{order_id}退款{amount}元"


agent = Agent(
    name="RefundAssistant",
    instructions="你是退款助手。查订单状态直接查；要执行退款必须调用 issue_refund 工具（该工具需要人工审批）。",
    tools=[check_order_status, issue_refund],
    model=default_model(),
    model_settings=ModelSettings(temperature=0),
)


def main() -> None:
    result = Runner.run_sync(agent, "帮我给订单A1001退款50元")

    # result.interruptions：模型想调用 issue_refund，但因为它标了 needs_approval，
    # 运行被"打断"在这一步，不会真的执行，而是把待审批的调用列出来等人决策。
    if result.interruptions:
        for interruption in result.interruptions:
            print(f"[待审批] 工具: {interruption.tool_name}, 参数: {interruption.arguments}")

        # 把当前的运行状态保存下来（to_state），这样即使审批流程是异步的
        # （比如人工审批要等客服主管在另一个系统里点"同意"，可能过了几分钟甚至几小时），
        # 也可以把这个 state 序列化存起来，之后再恢复继续跑。
        state = result.to_state()

        # 模拟人工审批：这里直接写死"同意"，真实场景这一步是人在审批界面点的按钮。
        approved = True
        for interruption in result.interruptions:
            if approved:
                state.approve(interruption)
                print(f"[审批通过] {interruption.tool_name}")
            else:
                state.reject(interruption)
                print(f"[审批拒绝] {interruption.tool_name}")

        # 带着审批决定，继续跑完这次对话——被批准的工具这时才会真正执行。
        final_result = Runner.run_sync(agent, state)
        print("\n最终结果:", final_result.final_output)
    else:
        print(result.final_output)


if __name__ == "__main__":
    main()
