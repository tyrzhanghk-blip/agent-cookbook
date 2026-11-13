"""
案例19（插件版）：用 openai-agents-skills 扩展实现同样的技能加载
与 main.py（手写版）的对比：
- 手写版：技能内容靠 Agent 自己调 read_skill 工具"拉取"（工具调用式）
- 插件版：SkillHooks 在每次模型调用前，把路由命中的技能直接"注入"上下文（prompt 注入式），
  另有 LLMSkillRouter 用一次轻量模型调用决定"这条消息该启用哪些技能"

两者目录格式相同（<skill_name>/SKILL.md，frontmatter: name/description），
所以 skills/ 目录直接复用。运行：
    uv run python cases/case19_agent_skills/plugin.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import Agent, ModelSettings, OpenAIChatCompletionsModel, Runner

from common.env import default_model, load_env

load_env()

from openai_agents_skills import (
    LLMSkillRouter,
    SkillHooks,
    SkillRegistry,
    SkillSource,
    load_skills_from_dir,
)

SKILLS_DIR = Path(__file__).parent / "skills"


async def main() -> None:
    # 1) 从 skills/ 目录加载（格式与手写版完全一致，直接复用；注意这是异步函数）
    file_skills = await load_skills_from_dir(SKILLS_DIR, SkillSource.PROJECT)
    print(f"已加载 {len(file_skills)} 个技能文件: {[s.name for s, _ in file_skills]}")

    # 2) 路由器：每条消息先用一次轻量模型调用决定启用哪些技能
    # 注意：这里要传 SDK 的 Model 实例（OpenAIChatCompletionsModel），
    # 不能传模型名字符串——router 内部会调 model.get_response()，字符串会直接失败
    #（失败时静默回退成"只注入技能清单"，模型就看不到 SOP 正文了）
    import os

    from openai import AsyncOpenAI

    router = LLMSkillRouter(
        model=OpenAIChatCompletionsModel(
            model=default_model(),
            openai_client=AsyncOpenAI(
                base_url=os.getenv("OPENAI_BASE_URL") or None,
                api_key=os.getenv("OPENAI_API_KEY"),
            ),
        ),
        model_settings=ModelSettings(temperature=0),
    )

    # 3) registry + hooks：Agent 挂上 hooks 后，命中的技能会在每次 LLM 调用前自动注入
    registry = SkillRegistry(router=router)
    for skill, _ in file_skills:
        registry.register(skill)

    agent = Agent(
        name="SkilledServicePlugin",
        instructions=(
            "你是电商客服。系统会自动为你注入相关的内部技能（SOP 文档），"
            "收到后严格按照技能文档里的流程和话术回答。"
        ),
        hooks=SkillHooks(registry=registry),
        model=default_model(),
        model_settings=ModelSettings(temperature=0),
    )

    questions = [
        "你们家卖手机吗？",                       # 不该命中任何技能
        "我买了个耳机想退款，8000 块的，多久能到账？",  # 应命中 refund_policy
        "我的快递显示签收了但我没收到，怎么办？",        # 应命中 logistics_escalation
    ]
    for q in questions:
        print(f"\n用户: {q}")
        result = await Runner.run(agent, q)
        print(f"客服: {result.final_output}")


if __name__ == "__main__":
    asyncio.run(main())