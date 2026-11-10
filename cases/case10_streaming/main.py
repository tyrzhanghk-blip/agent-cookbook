"""
案例10：流式输出（streaming）
目标：不要等模型把整段话全生成完才显示，而是像打字机一样边生成边显示——
真正的聊天产品几乎都需要这个，不然用户体验是"卡住几秒后一次性甩一大段字"。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import asyncio

from agents import Agent, ModelSettings, Runner
from agents.stream_events import RawResponsesStreamEvent, RunItemStreamEvent
from common.env import default_model, load_env

load_env()

agent = Agent(
    name="Assistant",
    instructions="你是助手，用中文回答问题。",
    model=default_model(),
    model_settings=ModelSettings(temperature=0),
)


async def main() -> None:
    # run_streamed 立刻返回一个 RunResultStreaming，真正的内容通过 stream_events() 异步产出。
    result = Runner.run_streamed(agent, "用三句话介绍一下流式输出的好处。")

    async for event in result.stream_events():
        # RawResponsesStreamEvent：底层模型原始的增量事件。
        # 注意 event.data.type 有很多种（reasoning 摘要、content_part 变化等），
        # 真正是"最终回答正文"的只有 response.output_text.delta，只打印这一种，
        # 否则会把模型的内部思考过程（reasoning）也当正文打出来，教学/生产都不该这样展示给用户。
        if isinstance(event, RawResponsesStreamEvent):
            if event.data.type == "response.output_text.delta":
                print(event.data.delta, end="", flush=True)
        # RunItemStreamEvent：更高层的事件，比如"一次工具调用完成了""一条消息生成完了"。
        elif isinstance(event, RunItemStreamEvent):
            if event.name == "tool_called":
                print(f"\n[工具调用: {event.item.raw_item.name}]", end="")

    print()  # 换行
    print("\n（以上内容是一个字一个字“打印”出来的，而不是等全部生成完再显示）")


if __name__ == "__main__":
    asyncio.run(main())
