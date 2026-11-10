"""
案例9：真实小产品 —— 订单客服工作台
目标：把前面所有案例学到的能力整合起来，做一个可以多轮对话的客服 Agent：
- 工具（案例2/3）：查订单、查物流
- context（案例4）：当前登录用户的身份信息，工具可读、模型不可见
- 对话记忆（案例4）：支持多轮追问
- as_tool（案例5）：FAQ 专家作为工具，被主客服按需调用
- handoff（案例6）：涉及退款这种敏感操作时，转交给专门的"退款专员"
- guardrail（案例7）：拦截与客服业务完全无关的请求
- tracing（案例8）：自定义日志处理器，记录每一步做了什么
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dataclasses import dataclass

from pydantic import BaseModel

from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    ModelSettings,
    RunContextWrapper,
    Runner,
    TracingProcessor,
    function_tool,
    input_guardrail,
    set_trace_processors,
    set_tracing_disabled,
)
from agents.tracing import Span, Trace

from common.env import default_model, load_env

load_env()


# ---------- context：当前登录用户，模型看不见，工具能读 ----------
@dataclass
class CurrentUser:
    user_id: str
    name: str


# ---------- 工具 ----------
_FAKE_ORDERS = {
    "A1001": {"status": "已发货", "item": "无线耳机", "tracking_no": "SF123456789"},
    "A1002": {"status": "待发货", "item": "机械键盘", "tracking_no": None},
}


@function_tool
def lookup_order(order_id: str) -> str:
    """根据订单号查询订单状态和商品信息。"""
    order = _FAKE_ORDERS.get(order_id)
    if not order:
        return f"没有找到订单 {order_id}"
    return f"订单{order_id}：商品「{order['item']}」，状态「{order['status']}」"


@function_tool
def lookup_tracking(order_id: str) -> str:
    """根据订单号查询物流单号。"""
    order = _FAKE_ORDERS.get(order_id)
    if not order or not order.get("tracking_no"):
        return f"订单 {order_id} 暂无物流单号（可能还未发货）"
    return f"订单{order_id}的物流单号是 {order['tracking_no']}"


@function_tool
def greet_user(wrapper: RunContextWrapper[CurrentUser]) -> str:
    """获取当前登录用户的称呼，用于个性化问候。"""
    return wrapper.context.name


# ---------- FAQ 专家（as_tool）----------
faq_agent = Agent(
    name="FaqAgent",
    instructions=(
        "你是电商 FAQ 专家，只回答退货政策、运费、会员权益这类通用规则问题，"
        "不处理具体某个订单的查询。规则：7天无理由退货；满99元免运费；会员享受生日折扣。"
    ),
    model=default_model(),
    model_settings=ModelSettings(temperature=0),
)

# ---------- 退款专员（handoff 目标）----------
refund_agent = Agent(
    name="RefundAgent",
    instructions=(
        "你是退款专员，专门处理退款申请。礼貌地询问订单号和退款原因，"
        "并说明退款会在1-3个工作日内到账。"
    ),
    model=default_model(),
    model_settings=ModelSettings(temperature=0),
)


# ---------- guardrail：拦截与客服业务无关的请求 ----------
class OffTopicCheck(BaseModel):
    is_off_topic: bool
    reasoning: str


topic_guard_agent = Agent(
    name="TopicGuard",
    instructions="判断用户的问题是否完全和电商客服业务（订单、物流、退款、FAQ）无关。",
    output_type=OffTopicCheck,
    model=default_model(),
    model_settings=ModelSettings(temperature=0),
)


@input_guardrail
async def block_off_topic(wrapper: RunContextWrapper, agent: Agent, input) -> GuardrailFunctionOutput:
    result = await Runner.run(topic_guard_agent, input, context=wrapper.context)
    check: OffTopicCheck = result.final_output
    return GuardrailFunctionOutput(output_info=check, tripwire_triggered=check.is_off_topic)


# ---------- 主客服 Agent ----------
customer_service_agent = Agent[CurrentUser](
    name="CustomerService",
    instructions=(
        "你是电商客服。可以用 lookup_order / lookup_tracking 查具体订单；"
        "通用规则问题（退货政策、运费、会员权益）调用 ask_faq 工具；"
        "如果用户明确要申请退款，handoff 给 RefundAgent 处理；"
        "首次对话可以用 greet_user 获取用户名字打个招呼。"
    ),
    tools=[
        lookup_order,
        lookup_tracking,
        greet_user,
        faq_agent.as_tool(tool_name="ask_faq", tool_description="查询退货政策、运费、会员权益等通用规则"),
    ],
    handoffs=[refund_agent],
    input_guardrails=[block_off_topic],
    model=default_model(),
    model_settings=ModelSettings(temperature=0),
)


# ---------- tracing：自定义日志 ----------
class CompactLoggingProcessor(TracingProcessor):
    def on_trace_start(self, trace: Trace) -> None:
        pass

    def on_trace_end(self, trace: Trace) -> None:
        pass

    def on_span_start(self, span: Span) -> None:
        name = type(span.span_data).__name__
        if name == "FunctionSpanData":
            print(f"    [调用工具] {span.span_data.name}")
        elif name == "HandoffSpanData":
            print(f"    [handoff] {span.span_data.from_agent} -> {span.span_data.to_agent}")

    def on_span_end(self, span: Span) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def force_flush(self) -> None:
        pass


def chat(history, user_input: str, user: CurrentUser):
    """跑一轮对话：带上历史（记忆），带上 context（身份），处理 guardrail 异常。"""
    print(f"\n用户: {user_input}")
    turn_input = history + [{"role": "user", "content": user_input}] if history else user_input
    try:
        result = Runner.run_sync(customer_service_agent, turn_input, context=user)
    except InputGuardrailTripwireTriggered as e:
        print(f"[被护栏拦截] {e.guardrail_result.output.output_info.reasoning}")
        return history
    print(f"客服（{result.last_agent.name}）: {result.final_output}")
    return result.to_input_list()


def main() -> None:
    set_tracing_disabled(False)
    set_trace_processors([CompactLoggingProcessor()])

    user = CurrentUser(user_id="u001", name="小明")
    history: list = []

    history = chat(history, "你好，帮我查一下订单A1001的状态", user)
    history = chat(history, "那它的物流单号是多少？", user)
    history = chat(history, "你们的退货政策是什么？", user)
    history = chat(history, "我要申请退款，订单号A1001", user)
    history = chat(history, "帮我写一首关于夏天的诗", user)  # 离题，会被拦截


if __name__ == "__main__":
    main()
