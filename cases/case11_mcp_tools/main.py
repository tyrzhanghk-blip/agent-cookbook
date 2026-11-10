"""
案例11：MCP 工具接入
目标：不用自己写 @function_tool，而是把 Agent 接到一个 MCP（Model Context Protocol）服务器，
直接复用服务器暴露出来的工具。MCP 是跨语言、跨厂商的标准协议——服务器可以是别人写的、甚至是别的语言写的，
Agent 侧完全不需要关心工具内部怎么实现。
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import Agent, ModelSettings, Runner
from agents.mcp import MCPServerStdio
from common.env import default_model, load_env

load_env()

SERVER_SCRIPT = Path(__file__).parent / "mcp_server.py"


async def main() -> None:
    # MCPServerStdio：通过标准输入输出和一个子进程通信，这个子进程就是我们的 mcp_server.py。
    # 生产环境常见的还有 MCPServerSse / MCPServerStreamableHttp（通过网络连远程 MCP 服务）。
    async with MCPServerStdio(
        name="KnowledgeBase",
        params={"command": sys.executable, "args": [str(SERVER_SCRIPT)]},
    ) as mcp_server:
        agent = Agent(
            name="Assistant",
            instructions="你是客服助手。涉及FAQ问题调用 search_faq 工具；需要当前时间就调用 get_server_time 工具。",
            mcp_servers=[mcp_server],
            model=default_model(),
            model_settings=ModelSettings(temperature=0),
        )

        r1 = await Runner.run(agent, "你们的退货政策是什么？")
        print("Q: 你们的退货政策是什么？")
        print("A:", r1.final_output)

        r2 = await Runner.run(agent, "现在服务器时间是多少？")
        print("\nQ: 现在服务器时间是多少？")
        print("A:", r2.final_output)


if __name__ == "__main__":
    asyncio.run(main())
