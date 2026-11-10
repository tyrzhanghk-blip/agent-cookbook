"""
案例16 共享模块：一个带工具的助手 Agent + 按 session_id 持久化对话历史。
CLI 和 Web 两种界面都复用这一份 Agent 定义，体现"界面只是壳子，核心是 Agent"。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import Agent, ModelSettings, Runner, function_tool
from agents.memory import SQLiteSession

from common.env import default_model, load_env

load_env()

DB_PATH = Path(__file__).parent / "conversations.db"


@function_tool
def get_current_time() -> str:
    """获取当前时间，格式 YYYY-MM-DD HH:MM:SS。"""
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


assistant = Agent(
    name="Assistant",
    instructions=(
        "你是一个友善的助手，记得住用户之前说过的话。"
        "如果用户问现在的时间，调用 get_current_time 工具。"
    ),
    tools=[get_current_time],
    model=default_model(),
    model_settings=ModelSettings(temperature=0),
)


async def areply(session_id: str, user_input: str) -> str:
    """跑一轮对话：按 session_id 加载/保存历史，返回助手的回复文本。

    这是整个案例唯一的业务入口，CLI 和 Web 两种界面都调用它。

    这里只提供异步版本，没有"每次调用都 asyncio.run() 一次"的同步封装，是刻意的：
    底层 AsyncOpenAI 客户端的连接池/锁会绑定在第一次用到的那个 event loop 上；
    如果每次调用都新建一个 loop 再关掉，上一轮的连接对象在下一轮就失效了，
    会报 "Event loop is closed" 或 "bound to a different event loop"。
    正确做法是：调用方（CLI / Web）自己维护**一个长期存在的 event loop**，
    整个进程/整个会话期间，所有 areply() 调用都丢进这同一个 loop 里跑——
    具体见 cli.py（loop.run_until_complete）和 web.py（run_coroutine_threadsafe）。
    """
    session = SQLiteSession(session_id=session_id, db_path=DB_PATH)
    result = await Runner.run(assistant, user_input, session=session)
    return result.final_output