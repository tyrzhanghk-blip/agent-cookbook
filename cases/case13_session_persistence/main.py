"""
案例13：会话持久化（Session）
目标：案例4里用 result.to_input_list() 手动拼历史，历史只存在内存变量里，进程一退出就丢了。
用 Session 把对话历史存到 SQLite，支持跨进程/跨重启保留，还能同时维护多个用户各自独立的会话。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import Agent, ModelSettings, Runner
from agents.memory import SQLiteSession
from common.env import default_model, load_env

load_env()

DB_PATH = Path(__file__).parent / "conversations.db"

agent = Agent(
    name="Assistant",
    instructions="你是一个友善的助手，记得住用户之前说过的话。",
    model=default_model(),
    model_settings=ModelSettings(temperature=0),
)


def main() -> None:
    # session_id 决定了"这是哪个用户/哪个对话"的历史。
    # db_path 指向磁盘文件：进程退出再重启，同一个 session_id 的历史依然存在。
    session = SQLiteSession(session_id="user_xiaoming", db_path=DB_PATH)

    # 传入 session 参数后，不用再自己拼 to_input_list()——
    # Runner 会自动从 session 读历史、自动把新一轮的结果写回 session。
    r1 = Runner.run_sync(agent, "我叫小明，我养了一只叫豆豆的猫。", session=session)
    print("用户: 我叫小明，我养了一只叫豆豆的猫。")
    print("助手:", r1.final_output)

    r2 = Runner.run_sync(agent, "我养的猫叫什么名字？", session=session)
    print("\n用户: 我养的猫叫什么名字？")
    print("助手:", r2.final_output)

    print(f"\n（对话历史已持久化到 {DB_PATH}，重新运行本脚本，Assistant 依然记得豆豆）")


if __name__ == "__main__":
    main()
