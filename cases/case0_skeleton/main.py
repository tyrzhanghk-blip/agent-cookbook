"""
案例0：骨架
目标：用最少的代码跑通一个 Agent 的最小闭环——创建 Agent，用 Runner 执行一次对话。
"""

import sys
from pathlib import Path

# 把仓库根目录加入 sys.path，这样才能 import common（各案例共用的小工具）。
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import Agent, Runner

from common.env import default_model, load_env

load_env()

# 一个 Agent 最少需要：name（名字）+ instructions（角色设定）
# model 可省略（走 SDK 默认模型）；如果你用的是内部网关，通常需要显式指定网关支持的模型名。
agent = Agent(
    name="Assistant",
    instructions="你是一个友善、简洁的助手，用中文回答问题。",
    model=default_model(),
)


def main() -> None:
    result = Runner.run_sync(agent, "用一句话介绍一下你自己。")
    print(result.final_output)


if __name__ == "__main__":
    main()
