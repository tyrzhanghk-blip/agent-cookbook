"""
案例18：批量数据转换管道（Transform Pipeline）
目标：Agent 不是只能做聊天机器人——真实生产里最常见的形态是"数据转换引擎"：
把一批非结构化的杂乱文本（客服工单），批量转换成严格 schema 的结构化记录。

管道流程（ETL 里的 T）：
  读取原始数据 -> 逐条转换（Agent + output_type）-> 校验 -> 失败重试/隔离 -> 汇总报告

工程重点：批量处理时"质量不齐"是常态——
- 有的记录转换失败（模型抽风/内容无意义）-> 重试一次，还不行就隔离到"人工待办"，不能让一条坏数据卡死整批
- 部分成功也要出报告：成功率、分类分布、失败清单
这综合了案例3的结构化输出、案例14的重试思路、案例15的校验思路。
"""

import json
import sys
import time
from enum import Enum
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pydantic import BaseModel, Field, field_validator

from agents import Agent, ModelSettings, Runner

from common.env import default_model, load_env

# case15 的教训：load_env 必须在本模块内部调用（import 时就要用 default_model() 建 Agent）
load_env()

DATA_PATH = Path(__file__).parent / "sample_data.json"
OUT_PATH = Path(__file__).parent / "transformed.json"
FAILED_PATH = Path(__file__).parent / "failed.json"


# ---------- 目标 schema：杂乱文本最终要变成什么样 ----------

# 枚举值用简单英文——模型输出必须和枚举值逐字匹配，中文+斜杠的值
# （如"退换货/退款"）模型很难精确复制，会导致校验失败反复重试（实测踩坑）。
# 中文含义放进 instructions 和下面的显示映射。
class Category(str, Enum):
    logistics = "logistics"      # 物流问题
    refund = "refund"            # 退换货/退款
    pricing = "pricing"          # 价格/优惠/发票
    membership = "membership"    # 会员/账号
    product = "product"          # 商品咨询
    complaint = "complaint"      # 投诉/不满
    other = "other"              # 其他


CATEGORY_CN = {
    "logistics": "物流问题", "refund": "退换货/退款", "pricing": "价格/优惠/发票",
    "membership": "会员/账号", "product": "商品咨询", "complaint": "投诉/不满", "other": "其他",
}


class Sentiment(str, Enum):
    positive = "positive"    # 正面
    neutral = "neutral"      # 中性
    negative = "negative"    # 负面


SENTIMENT_CN = {"positive": "正面", "neutral": "中性", "negative": "负面"}


class TicketRecord(BaseModel):
    """一条结构化后的工单记录——这就是整条管道的"产品"。"""
    category: Category
    sentiment: Sentiment
    order_id: str | None = Field(default=None, description="文本里提到的订单号，如 A2001；没有就是 None")
    urgency: int = Field(ge=1, le=5, description="紧急程度 1-5，涉及资金损失/投诉升级为 4-5")
    summary: str = Field(min_length=5, description="一句话概括诉求，不超过30字")

    @field_validator("order_id", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        """模型有时会给空串而不是 null——统一归一化，下游就不用两种都判断。"""
        return v or None


# ---------- 转换 Agent：单条文本 -> TicketRecord ----------

transform_agent = Agent(
    name="TicketTransformer",
    instructions=(
        "你是客服工单结构化助手。把给你的用户原话转换成一条工单记录，严格遵守 schema：\n"
        "- category 只能取以下值之一（含义）：logistics=物流问题、refund=退换货/退款、"
        "pricing=价格/优惠/发票、membership=会员/账号、product=商品咨询、"
        "complaint=投诉/不满、other=其他；必须逐字一致，拿不准选 other\n"
        "- sentiment 只能取 positive/neutral/negative 之一\n"
        "- order_id：原文明确提到订单号才填（如 A2001），不要编造\n"
        "- urgency：普通咨询 1-2，有问题需要处理 3，涉及资金/投诉/隐私 4-5\n"
        "- summary：客观概括诉求，不带情绪词\n"
        "如果原文完全无意义（比如纯表情、灌水），summary 填「无效内容」，category 选 other。"
    ),
    output_type=TicketRecord,
    model=default_model(),
    model_settings=ModelSettings(temperature=0),
)


def transform_one(item: dict) -> tuple[TicketRecord | None, str | None]:
    """转换单条：失败自动重试一次；两次都失败返回 (None, 错误原因)。"""
    last_err = ""
    for attempt in (1, 2):  # 复用案例14的思路：外层兜底重试
        try:
            result = Runner.run_sync(transform_agent, item["text"])
            record: TicketRecord = result.final_output
            # 业务校验：pydantic 已保证字段合法，这里补语义层面的人工规则
            if record.category == Category.other and record.summary == "无效内容":
                pass  # 合法的"识别为无效内容"结果，不算失败（和转换失败区分开）
            return record, None
        except Exception as e:  # 结构化输出不合法/网络/超时，来源很杂，宽捕获
            last_err = f"{type(e).__name__}: {e}"
            if attempt == 1:
                print(f"    第1次失败（{item['id']}），重试: {last_err[:80]}")
    return None, last_err


def main() -> None:
    raw_items = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    # uv run main.py 5 -> 只处理前5条（调试/演示用）
    if len(sys.argv) > 1:
        raw_items = raw_items[: int(sys.argv[1])]
    print(f"读取 {len(raw_items)} 条原始工单，开始批量转换...\n")

    transformed: list[dict] = []
    failed: list[dict] = []
    start = time.time()

    for i, item in enumerate(raw_items, 1):
        record, err = transform_one(item)
        if record:
            transformed.append({"source_id": item["id"], **record.model_dump(mode="json")})
            tag = "无效内容" if record.summary == "无效内容" else "OK"
            print(f"  [{i:2}/{len(raw_items)}] {item['id']} -> {CATEGORY_CN[record.category.value]} / {SENTIMENT_CN[record.sentiment.value]} / 紧急度{record.urgency} ({tag})")
        else:
            failed.append({"source_id": item["id"], "text": item["text"], "error": err})
            print(f"  [{i:2}/{len(raw_items)}] {item['id']} -> [失败] {err[:80]}")

    # ---------- 汇总报告：部分成功也要有完整的账 ----------
    elapsed = time.time() - start
    print("\n" + "=" * 50)
    print("汇总报告")
    print(f"  总数 {len(raw_items)} | 成功 {len(transformed)} | 失败 {len(failed)} | 耗时 {elapsed:.1f}s")

    if transformed:
        print("\n  分类分布:")
        cat_count: dict[str, int] = {}
        for t in transformed:
            cat_count[t["category"]] = cat_count.get(t["category"], 0) + 1
        for cat, n in sorted(cat_count.items(), key=lambda x: -x[1]):
            print(f"    {CATEGORY_CN.get(cat, cat)}: {n}")
        neg = sum(1 for t in transformed if t["sentiment"] == "negative")
        print(f"  负面占比: {neg}/{len(transformed)}")
        high = [t["source_id"] for t in transformed if t["urgency"] >= 4]
        print(f"  高紧急（>=4）: {', '.join(high) if high else '无'}")

    if failed:
        print("\n  失败清单（人工待办）:")
        for f in failed:
            print(f"    {f['source_id']}: {f['error'][:80]}")

    OUT_PATH.write_text(json.dumps(transformed, ensure_ascii=False, indent=2), encoding="utf-8")
    FAILED_PATH.write_text(json.dumps(failed, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n产物: {OUT_PATH.name}（{len(transformed)} 条） / {FAILED_PATH.name}（{len(failed)} 条）")
    print("失败的不会丢——隔离出来留给人工处理，这就是管道的'部分成功'策略。")


if __name__ == "__main__":
    main()