"""
案例1：指令（instructions）
目标：instructions 不一定是写死的字符串，还可以是一个函数，根据运行时的 context 动态生成。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import Agent, Runner
from common.env import default_model, load_env

load_env()

from dataclasses import dataclass

from agents import RunContextWrapper


@dataclass
class UserInfo:
    name: str
    level: str  # "beginner" | "expert"


def build_instructions(wrapper: RunContextWrapper[UserInfo], agent: Agent) -> str:
    user = wrapper.context
    if user.level == "beginner":
        return f"你是给新手讲解编程概念的老师，正在给{user.name}解释。多用类比，少用术语。"
    return f"你是资深技术顾问，正在给{user.name}解释。可以直接用术语，追求精确和简洁。"


# instructions 传入函数而不是字符串，SDK 会在每次运行时调用它，传入 context 和 agent 自身。
agent = Agent[UserInfo](
    name="Teacher",
    instructions=build_instructions,
    model=default_model(),
)


def main() -> None:
    beginner = UserInfo(name="小白", level="beginner")
    expert = UserInfo(name="老王", level="expert")

    r1 = Runner.run_sync(agent, "什么是递归？", context=beginner)
    print("=== 给新手的回答 ===")
    print(r1.final_output)

    r2 = Runner.run_sync(agent, "什么是递归？", context=expert)
    print("\n=== 给专家的回答 ===")
    print(r2.final_output)


if __name__ == "__main__":
    main()
