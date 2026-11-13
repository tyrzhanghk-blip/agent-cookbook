"""
案例19：Agent Skills —— 领域知识按需加载（Claude Code Skill 机制复刻）
目标：前面案例的 instructions 都是"一次性把所有知识塞给模型"。但真实系统里
领域知识（SOP、政策、规范）会越积越多——全塞进 instructions 会：
  1. 浪费 token（每轮对话都带着全部知识，哪怕这次用不上）
  2. 稀释注意力（模型在一堆无关 SOP 里找重点）
  3. 难以维护（改一条政策要动 Agent 代码）

解法就是 Skill 机制（Claude Code / Cursor rules 都是这个思路）：
  - 每个领域的知识写成独立的 SKILL.md 文件（frontmatter: name + description）
  - Agent 只内置一个"技能索引"（name + description，很便宜）
  - 对话中按需用 read_skill 工具加载完整内容（贵，但只在需要时发生）

本案例的客服 Agent 内置 3 个技能：退款政策 / 物流异常升级 / VIP 服务规范。
问普通问题时一个技能都不加载；问到退款政策才去读 refund_policy。
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import Agent, ModelSettings, Runner, function_tool

from common.env import default_model, load_env

load_env()

SKILLS_DIR = Path(__file__).parent / "skills"


# ---------- 技能加载与解析 ----------

def _parse_skill(path: Path) -> dict:
    """解析 SKILL.md：frontmatter 里的 name/description + 正文。"""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        return {"name": path.parent.name, "description": "", "body": text}
    meta, body = m.group(1), m.group(2)
    name = re.search(r"^name:\s*(.+)$", meta, re.MULTILINE)
    desc = re.search(r"^description:\s*(.+)$", meta, re.MULTILINE)
    return {
        "name": name.group(1).strip() if name else path.parent.name,
        "description": desc.group(1).strip() if desc else "",
        "body": body.strip(),
    }


def _load_skills() -> dict[str, dict]:
    return {
        s["name"]: s
        for s in (_parse_skill(p / "SKILL.md") for p in sorted(SKILLS_DIR.iterdir()) if p.is_dir())
    }


# ---------- 工具：技能索引（便宜）与按需加载（贵） ----------

@function_tool
def list_skills() -> str:
    """列出当前可用的技能清单（只有名字和一句话描述）。先看这个，再决定读哪个。"""
    skills = _load_skills()
    print("  [工具] list_skills")
    return "\n".join(f"- {s['name']}: {s['description']}" for s in skills.values())


@function_tool
def read_skill(name: str) -> str:
    """读取指定技能的完整内容（标准作业流程）。name 必须是 list_skills 里列出的名字。"""
    print(f"  [工具] read_skill({name})")
    skills = _load_skills()
    if name not in skills:
        return f"没有叫 {name} 的技能，可用: {', '.join(skills)}"
    return skills[name]["body"]


# ---------- Agent：instructions 只放"路由"，不放知识 ----------

customer_service = Agent(
    name="SkilledService",
    instructions=(
        "你是电商客服。你掌握若干内部技能（SOP 文档），但不要凭记忆回答政策/流程类问题：\n"
        "1. 遇到政策、退款、物流异常、VIP 权益等问题，先调用 list_skills 查看有什么技能\n"
        "2. 用 read_skill 读取相关技能的完整内容\n"
        "3. 严格按照技能文档里的流程和话术回答\n"
        "普通闲聊或与政策无关的问题直接回答，不要乱加载技能。"
    ),
    tools=[list_skills, read_skill],
    model=default_model(),
    model_settings=ModelSettings(temperature=0),
)


def chat(user_input: str) -> None:
    print(f"\n用户: {user_input}")
    result = Runner.run_sync(customer_service, user_input)
    print(f"客服: {result.final_output}")


def main() -> None:
    # 第一轮：普通问题，不该加载任何技能
    chat("你们家卖手机吗？")

    # 第二轮：退款政策，应触发 list_skills -> read_skill(refund_policy)
    chat("我买了个耳机想退款，8000 块的，多久能到账？")

    # 第三轮：VIP 权益，应触发 read_skill(vip_service)
    chat("我是 VIP 吧？我有什么专属权益？")

    # 第四轮：物流异常，应触发 read_skill(logistics_escalation)
    chat("我的快递显示签收了但我没收到，怎么办？")


if __name__ == "__main__":
    main()
