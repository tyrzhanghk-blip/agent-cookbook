"""
案例15：评估与测试
目标：给 Agent 写回归测试，分两层——
  1. 纯逻辑层（工具函数本身）：不涉及模型，秒级运行，每次改代码都该跑。
  2. Agent 行为层（真的调用模型）：验证"给定输入，Agent 的行为/输出结构符合预期"，
     不去断言死板的文字内容（模型的措辞每次会变），而是断言结构化的、可验证的东西：
     - output_type 的字段是否合理
     - 该不该调用某个工具
     - 该不该被 guardrail 拦截
这一层慢、吃 token，适合放在"改了 prompt / 加了工具之后"手动跑，而不是每次 commit 都跑。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pydantic import BaseModel

from agents import (
    Agent,
    GuardrailFunctionOutput,
    ModelSettings,
    RunContextWrapper,
    Runner,
    function_tool,
    input_guardrail,
)
from common.env import default_model, load_env

# core.py 一被 import 就会建 Agent（用到 default_model()），所以环境变量必须在这里加载，
# 不能依赖"调用方在 import 我之前记得调用 load_env()"这种脆弱的顺序假设。
load_env()


# ---------- 1. 纯逻辑层：核心业务逻辑和 Agent 工具解耦，方便单独测试 ----------
def calc_shipping_fee(order_amount: float) -> float:
    """订单满99元免运费，否则收8元运费。"""
    if order_amount >= 99:
        return 0.0
    return 8.0


@function_tool
def get_shipping_fee(order_amount: float) -> str:
    """根据订单金额计算运费。

    Args:
        order_amount: 订单金额，单位元。
    """
    fee = calc_shipping_fee(order_amount)
    return f"{fee}元" if fee else "免运费"


shipping_agent = Agent(
    name="ShippingAgent",
    instructions="你是购物助手，涉及运费问题时调用 get_shipping_fee 工具获取真实运费，不要自己估算。",
    tools=[get_shipping_fee],
    model=default_model(),
    model_settings=ModelSettings(temperature=0),
)


# ---------- 2. Agent 行为层：带 output_type 的结构化输出 ----------
class OrderSummary(BaseModel):
    order_amount: float
    shipping_fee: float
    free_shipping: bool


summary_agent = Agent(
    name="SummaryAgent",
    instructions=(
        "根据输入的订单金额和运费信息，整理成结构化订单摘要。free_shipping 表示运费是否为0。"
    ),
    output_type=OrderSummary,
    model=default_model(),
    model_settings=ModelSettings(temperature=0),
)


# ---------- 3. Agent 行为层：guardrail ----------
class OffTopicCheck(BaseModel):
    is_off_topic: bool


topic_guard_agent = Agent(
    name="TopicGuard",
    instructions="判断用户的问题是否和购物（下单、运费、商品）无关。",
    output_type=OffTopicCheck,
    model=default_model(),
    model_settings=ModelSettings(temperature=0),
)


@input_guardrail
async def block_off_topic(wrapper: RunContextWrapper, agent: Agent, input) -> GuardrailFunctionOutput:
    result = await Runner.run(topic_guard_agent, input, context=wrapper.context)
    check: OffTopicCheck = result.final_output
    return GuardrailFunctionOutput(output_info=check, tripwire_triggered=check.is_off_topic)


guarded_shopping_agent = shipping_agent.clone(
    name="GuardedShoppingAgent",
    input_guardrails=[block_off_topic],
)
