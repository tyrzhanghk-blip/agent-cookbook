"""
案例2：工具（基础）
目标：给 Agent 一个自定义工具（function_tool），让它学会在需要时调用外部能力，而不是靠瞎编。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import Agent, Runner
from common.env import default_model, load_env

load_env()

from agents import function_tool


@function_tool
def get_weather(city: str) -> str:
    """查询指定城市的天气。

    Args:
        city: 城市名称，例如"北京"。
    """
    # 真实项目里这里会调用天气 API；教程里用一个假数据模拟。
    fake_weather = {"北京": "晴，18°C", "上海": "多云，22°C"}
    return fake_weather.get(city, f"没有{city}的天气数据")


agent = Agent(
    name="WeatherBot",
    instructions="你是天气助手。遇到查天气的问题，必须调用 get_weather 工具获取真实数据，不要凭空编造。",
    tools=[get_weather],
    model=default_model(),
)


def main() -> None:
    result = Runner.run_sync(agent, "北京今天天气怎么样？适合出门吗？")
    print(result.final_output)


if __name__ == "__main__":
    main()
