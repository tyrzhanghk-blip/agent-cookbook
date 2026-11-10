"""
案例3：工具（进阶）
目标：组合多个工具解决一个复合问题；用 output_type 让 Agent 输出结构化数据（Pydantic 模型）。

坑：让同一个 Agent 在一轮里"既调用多个工具、又产出严格结构化输出"，对模型要求很高——
能力弱一点的模型容易走捷径，直接按字段名编一个答案，不真正调用工具。
更稳妥的工程做法：拆成两步/两个 Agent：
  1. researcher：只管调用工具、把真实结果说清楚（不要求结构化输出，降低它的负担）。
  2. formatter：只管把一段文本整理成结构化字段（不需要调用任何工具，降低它的负担）。
这也是多 Agent 协作的雏形，后面案例5/6会讲更正式的组织方式（as_tool / handoff）。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import Agent, ModelSettings, Runner
from common.env import default_model, load_env

load_env()

from pydantic import BaseModel

from agents import function_tool


@function_tool
def get_weather(city: str) -> str:
    """查询指定城市的天气，返回类似"多云，22°C"的字符串。"""
    fake_weather = {"北京": "晴，18°C", "上海": "多云，22°C，有小雨"}
    return fake_weather.get(city, f"没有{city}的天气数据")


@function_tool
def get_clothing_advice(temperature_c: int) -> str:
    """根据气温（摄氏度）给出穿衣建议。

    Args:
        temperature_c: 气温，单位摄氏度，例如22。
    """
    if temperature_c >= 25:
        return "短袖短裤即可"
    if temperature_c >= 15:
        return "长袖或薄外套"
    return "厚外套，注意保暖"


class TravelPlan(BaseModel):
    city: str
    weather_summary: str
    clothing_advice: str
    should_bring_umbrella: bool


# 第一个 Agent：专心调用工具，输出就是普通文本，不掺结构化约束。
researcher = Agent(
    name="Researcher",
    instructions=(
        "依次调用 get_weather(city) 和 get_clothing_advice(temperature_c)，"
        "把这两个工具的真实返回结果原样列出来，不要编造、不要省略。"
    ),
    tools=[get_weather, get_clothing_advice],
    model=default_model(),
    model_settings=ModelSettings(temperature=0),
)

# 第二个 Agent：专心把一段文本整理成结构化字段，不需要调用任何工具。
formatter = Agent(
    name="Formatter",
    instructions=(
        "把输入的调研结果整理成结构化字段，只能使用输入里出现过的信息，不要新增内容。"
        "should_bring_umbrella 根据天气文本里是否出现雨字判断。"
    ),
    output_type=TravelPlan,
    model=default_model(),
    model_settings=ModelSettings(temperature=0),
)


def main() -> None:
    city = "上海"
    research_result = Runner.run_sync(researcher, f"帮我调研{city}明天的天气和穿衣建议")
    print("=== 调研阶段（工具调用）===")
    print(research_result.final_output)

    format_result = Runner.run_sync(
        formatter, f"城市：{city}\n调研结果：{research_result.final_output}"
    )
    plan: TravelPlan = format_result.final_output
    print("\n=== 格式化阶段（结构化输出）===")
    print(f"城市：{plan.city}")
    print(f"天气：{plan.weather_summary}")
    print(f"穿衣建议：{plan.clothing_advice}")
    print(f"要带伞：{'是' if plan.should_bring_umbrella else '否'}")


if __name__ == "__main__":
    main()
