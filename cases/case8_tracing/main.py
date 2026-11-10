"""
案例8：可观测性（tracing）
目标：理解 Agent 运行时的 trace/span 结构，并学会接入自己的日志/监控，而不依赖 OpenAI 官方 tracing 后端
（很多内部网关的 key 没有权限上报到官方后端，案例0里我们已经把它关掉了）。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import Agent, ModelSettings, Runner
from common.env import default_model, load_env

load_env()

from agents import (
    TracingProcessor,
    function_tool,
    set_trace_processors,
    set_tracing_disabled,
)
from agents.tracing import Span, Trace


class LoggingProcessor(TracingProcessor):
    """一个最小的自定义 tracing 处理器：把 trace/span 的生命周期打印出来。

    真实项目里，可以把这些事件发到自己的日志系统/APM（比如写文件、发 Kafka、推 Prometheus）。
    """

    def on_trace_start(self, trace: Trace) -> None:
        print(f"[trace start] {trace.name} (id={trace.trace_id})")

    def on_trace_end(self, trace: Trace) -> None:
        print(f"[trace end]   {trace.name}")

    def on_span_start(self, span: Span) -> None:
        print(f"  [span start] {type(span.span_data).__name__}")

    def on_span_end(self, span: Span) -> None:
        print(f"  [span end]   {type(span.span_data).__name__}")

    def shutdown(self) -> None:
        pass

    def force_flush(self) -> None:
        pass


@function_tool
def add(a: int, b: int) -> int:
    """两个整数相加。"""
    return a + b


def main() -> None:
    # 本案例要演示 tracing，所以显式打开它（覆盖 common/env.py 里对网关场景的默认关闭），
    # 并换成我们自己的处理器，而不是上报到 OpenAI 官方后端。
    set_tracing_disabled(False)
    # 用 set_trace_processors 整体替换默认处理器列表（里面包含会上报官方后端的那个），
    # 换成只有我们自己的处理器，避免网关 key 没权限导致的 401 噪音。
    set_trace_processors([LoggingProcessor()])

    agent = Agent(
        name="MathBot",
        instructions="你是算术助手，必须调用 add 工具来做加法，不要自己心算。",
        tools=[add],
        model=default_model(),
        model_settings=ModelSettings(temperature=0),
    )

    result = Runner.run_sync(agent, "17 加 25 等于多少？")
    print("\n最终回答:", result.final_output)


if __name__ == "__main__":
    main()
