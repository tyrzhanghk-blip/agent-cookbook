"""
案例5：多专家 as_tool
目标：把专家 Agent 包装成工具（as_tool），交给一个"调度"Agent 按需调用。
适合场景：调度者需要对结果做二次加工/汇总，或者一次任务可能要同时问多个专家。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import Agent, ModelSettings, Runner
from common.env import default_model, load_env

load_env()


translator_zh_en = Agent(
    name="ZhToEnTranslator",
    instructions="把用户给的中文翻译成英文，只输出翻译结果，不要解释。",
    model=default_model(),
    model_settings=ModelSettings(temperature=0),
)

translator_en_zh = Agent(
    name="EnToZhTranslator",
    instructions="把用户给的英文翻译成中文，只输出翻译结果，不要解释。",
    model=default_model(),
    model_settings=ModelSettings(temperature=0),
)

# as_tool() 把一个 Agent 包装成普通的 function tool：
# - tool_name / tool_description 决定调度者"看到"的工具说明
# - 调度者把这个专家当黑盒工具调用，拿到的是专家的 final_output（字符串）
triage_agent = Agent(
    name="Concierge",
    instructions=(
        "你是多语言助手。如果用户要把中文翻成英文，调用 translate_zh_to_en 工具；"
        "如果要把英文翻成中文，调用 translate_en_to_zh 工具；"
        "拿到翻译结果后，用一句话礼貌地把结果呈现给用户。"
    ),
    tools=[
        translator_zh_en.as_tool(
            tool_name="translate_zh_to_en",
            tool_description="把一段中文翻译成英文",
        ),
        translator_en_zh.as_tool(
            tool_name="translate_en_zh_zh",
            tool_description="把一段英文翻译成中文",
        ),
    ],
    model=default_model(),
    model_settings=ModelSettings(temperature=0),
)


def main() -> None:
    r1 = Runner.run_sync(triage_agent, "帮我把“今天天气真好”翻译成英文")
    print("请求1:", r1.final_output)

    r2 = Runner.run_sync(triage_agent, "帮我把 'Have a nice day' 翻译成中文")
    print("请求2:", r2.final_output)


if __name__ == "__main__":
    main()
