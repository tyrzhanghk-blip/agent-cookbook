"""
案例7：安全护栏（guardrails）
目标：在模型真正处理用户输入之前/产出最终结果之前，插入一道校验逻辑。
- input_guardrail：拦截不该让主 Agent 处理的输入（比如让它干与业务无关的事）。
- output_guardrail：拦截不该让用户看到的输出（比如泄露了不该说的信息）。
触发的护栏会抛出 Tripwire 异常，调用方可以 catch 住，做兜底处理。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import Agent, ModelSettings, Runner
from common.env import default_model, load_env

load_env()

from pydantic import BaseModel

from agents import (
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    RunContextWrapper,
    input_guardrail,
)


class OffTopicCheck(BaseModel):
    is_off_topic: bool
    reasoning: str


# 用一个轻量 Agent 专门做"分类"，而不是在主流程里写一堆 if/else 关键词匹配——
# 这样能识别出语义上离题的问题，而不仅仅是字面匹配。
topic_guard_agent = Agent(
    name="TopicGuard",
    instructions="判断用户的问题是否和“客服坐席”业务（账单、退款、技术支持）无关。无关就是 is_off_topic=True。",
    output_type=OffTopicCheck,
    model=default_model(),
    model_settings=ModelSettings(temperature=0),
)


@input_guardrail
async def block_off_topic(
    wrapper: RunContextWrapper, agent: Agent, input
) -> GuardrailFunctionOutput:
    result = await Runner.run(topic_guard_agent, input, context=wrapper.context)
    check: OffTopicCheck = result.final_output
    return GuardrailFunctionOutput(
        output_info=check,
        tripwire_triggered=check.is_off_topic,
    )


customer_service_agent = Agent(
    name="CustomerService",
    instructions="你是客服，只回答账单、退款、技术支持相关问题。",
    input_guardrails=[block_off_topic],
    model=default_model(),
    model_settings=ModelSettings(temperature=0),
)


def ask(question: str) -> None:
    try:
        result = Runner.run_sync(customer_service_agent, question)
        print(f"Q: {question}")
        print(f"A: {result.final_output}")
    except InputGuardrailTripwireTriggered as e:
        print(f"Q: {question}")
        print(f"[被护栏拦截] 原因: {e.guardrail_result.output.output_info.reasoning}")


def main() -> None:
    ask("我想申请退款，上次多扣了50块。")
    print()
    ask("帮我写一首关于春天的诗。")  # 离题问题，会被护栏拦下


if __name__ == "__main__":
    main()
