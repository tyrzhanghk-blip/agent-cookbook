"""
案例6：handoff
目标：把整个对话的控制权从一个 Agent 转交给另一个 Agent（而不是像 as_tool 那样只借用结果）。
典型场景：客服分诊——前台 Agent 判断问题类型，交给对应的专科 Agent 继续对话。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import Agent, ModelSettings, Runner
from common.env import default_model, load_env

load_env()


billing_agent = Agent(
    name="BillingAgent",
    instructions="你是账单专员，只负责回答账单、付款、退款相关问题，语气专业耐心。",
    model=default_model(),
    model_settings=ModelSettings(temperature=0),
)

tech_support_agent = Agent(
    name="TechSupportAgent",
    instructions="你是技术支持专员，只负责回答登录、报错、功能故障相关问题，给出排查步骤。",
    model=default_model(),
    model_settings=ModelSettings(temperature=0),
)

# handoffs=[...]：triage_agent 判断完问题类型后，会把对话直接"转交"给对应的专科 Agent，
# 之后的对话由专科 Agent 全权负责，不再回到 triage_agent（除非专科 Agent 自己又 handoff 回去）。
triage_agent = Agent(
    name="TriageAgent",
    instructions=(
        "你是客服前台。判断用户问题属于账单问题还是技术问题，然后 handoff 给对应的专员处理，"
        "自己不要直接回答具体问题。"
    ),
    handoffs=[billing_agent, tech_support_agent],
    model=default_model(),
    model_settings=ModelSettings(temperature=0),
)


def main() -> None:
    r1 = Runner.run_sync(triage_agent, "我上个月被多扣了钱，能退款吗？")
    print("=== 账单问题 ===")
    print("最终处理的 Agent:", r1.last_agent.name)
    print(r1.final_output)

    r2 = Runner.run_sync(triage_agent, "我登录的时候一直提示密码错误，但密码没改过。")
    print("\n=== 技术问题 ===")
    print("最终处理的 Agent:", r2.last_agent.name)
    print(r2.final_output)


if __name__ == "__main__":
    main()
