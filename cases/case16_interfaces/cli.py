"""
案例16（CLI 界面）：在终端里跟 Agent 聊天。
核心逻辑全部在 agent.py 的 areply() 里，这里只负责"读用户输入、打印回复"。

注意：这里手动管理一个长期存在的 event loop，整个会话期间只用这一个 loop
跑所有的 areply() 调用，而不是每轮对话都 asyncio.run()（创建新 loop）。
原因：底层 AsyncOpenAI 客户端的连接池/锁绑定在第一次用到的那个 loop 上，
如果每轮对话都新建一个 loop，上一轮的 loop 关闭后，这些连接对象就失效了，
下一轮会报 "Event loop is closed" / "bound to a different event loop"。
"""

import asyncio

from agent import areply


def main() -> None:
    session_id = input("请输入你的用户名（用于区分各自的对话历史，回车默认 guest）: ").strip() or "guest"
    print(f"\n已进入对话（session_id={session_id}），输入 exit 或 quit 退出。\n")

    loop = asyncio.new_event_loop()
    try:
        while True:
            try:
                user_input = input("你: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n再见！")
                break

            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit"}:
                print("再见！")
                break

            answer = loop.run_until_complete(areply(session_id, user_input))
            print(f"助手: {answer}\n")
    finally:
        loop.close()


if __name__ == "__main__":
    main()
