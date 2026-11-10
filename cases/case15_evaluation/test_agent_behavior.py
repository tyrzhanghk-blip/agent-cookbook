"""
第二层测试：真的调用模型，验证"行为"而不是"文字"。
慢、吃 token，适合改完 prompt / 加完工具之后手动跑一遍，而不是每次 commit 都跑
（可以用 pytest -m llm 单独挑出来跑，见 pyproject.toml 里的 marker 配置）。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import pytest

from agents import Runner
from agents.exceptions import InputGuardrailTripwireTriggered

from cases.case15_evaluation.core import (
    OrderSummary,
    guarded_shopping_agent,
    shipping_agent,
    summary_agent,
)

pytestmark = pytest.mark.llm


def test_shipping_agent_calls_tool_not_guesses():
    """断言"行为"：Agent 的回答里必须出现工具算出来的真实数字（8元），
    而不是去断言模型用什么措辞说这句话——措辞每次跑都会变，断言数字更稳健。
    """
    result = Runner.run_sync(shipping_agent, "我买了50元的东西，运费多少？")
    assert "8" in result.final_output


def test_shipping_agent_recognizes_free_shipping():
    result = Runner.run_sync(shipping_agent, "我买了120元的东西，需要付运费吗？")
    assert "免运费" in result.final_output or "0" in result.final_output


def test_summary_agent_output_schema():
    """断言"结构"：output_type 的字段类型和取值是否合理，而不是断言具体文案。"""
    result = Runner.run_sync(summary_agent, "订单金额120元，运费0元")
    summary: OrderSummary = result.final_output
    assert isinstance(summary, OrderSummary)
    assert summary.order_amount == 120
    assert summary.free_shipping is True


def test_guardrail_blocks_off_topic_question():
    """断言"该不该被拦截"：离题问题必须触发 guardrail。"""
    with pytest.raises(InputGuardrailTripwireTriggered):
        Runner.run_sync(guarded_shopping_agent, "帮我写一首关于秋天的诗")


def test_guardrail_allows_on_topic_question():
    """同样重要：正常购物问题不应该被误拦截（避免护栏太敏感把正常用户挡在外面）。"""
    result = Runner.run_sync(guarded_shopping_agent, "我买了50元的东西，运费多少？")
    assert "8" in result.final_output
