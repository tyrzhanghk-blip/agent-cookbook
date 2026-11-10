"""
案例4：上下文与记忆
目标：区分两种"状态"——
  1. context：开发者传给工具/instructions 的业务数据，模型看不见，只有你的代码能读。
  2. 对话历史：模型真正"记住"的东西，需要你显式把上一轮的内容带进下一轮。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import Agent, ModelSettings, Runner
from common.env import default_model, load_env

load_env()

from dataclasses import dataclass

from agents import RunContextWrapper, function_tool


@dataclass
class UserSession:
    user_id: str
    vip: bool


@function_tool
def get_discount(wrapper: RunContextWrapper[UserSession]) -> str:
    """查询当前用户能享受的折扣。"""
    # 工具可以读取 context（第一个参数会被自动注入 RunContextWrapper），
    # 这里的 vip 信息模型自己是看不到的，必须靠工具去读。
    session = wrapper.context
    return "9折（VIP专属）" if session.vip else "无折扣"


agent = Agent[UserSession](
    name="ShopAssistant",
    instructions="你是购物助手。涉及折扣问题时调用 get_discount 工具获取真实折扣。",
    tools=[get_discount],
    model=default_model(),
    model_settings=ModelSettings(temperature=0),
)


def demo_context() -> None:
    print("=== context：业务数据，模型看不见，工具能读 ===")
    session = UserSession(user_id="u001", vip=True)
    result = Runner.run_sync(agent, "我能有什么折扣？", context=session)
    print(result.final_output)


def demo_conversation_memory() -> None:
    print("\n=== 对话历史：模型靠它“记住”上一轮说了什么 ===")
    session = UserSession(user_id="u001", vip=False)

    # 第一轮
    r1 = Runner.run_sync(agent, "我叫小明，想买一件外套。", context=session)
    print("用户: 我叫小明，想买一件外套。")
    print("助手:", r1.final_output)

    # 关键：用 r1.to_input_list() 把"第一轮的完整上下文"接到第二轮的输入里，
    # 模型才能"记住"小明说过的话。如果不这样做，第二轮是全新的、没有记忆的对话。
    next_input = r1.to_input_list() + [{"role": "user", "content": "我刚才说我叫什么名字？"}]
    r2 = Runner.run_sync(agent, next_input, context=session)
    print("用户: 我刚才说我叫什么名字？")
    print("助手:", r2.final_output)


def main() -> None:
    demo_context()
    demo_conversation_memory()


if __name__ == "__main__":
    main()
