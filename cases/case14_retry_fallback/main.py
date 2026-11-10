"""
案例14：重试与降级策略
目标：案例3里踩过真实的坑——网关偶发超时/卡住。这个案例把"怎么应对不可靠的模型调用"系统化：
1. 自动重试：ModelRetrySettings，网络抖动/偶发超时时，SDK 自动重试几次，不用你手写循环。
2. 手动降级：主模型调用全部失败后，换一个更简单/更快的模型再试一次，保证"宁可降级也不整个挂掉"。
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import Agent, ModelRetrySettings, ModelSettings, Runner
from common.env import default_model, load_env

load_env()


def build_agent(model: str, timeout: float, max_retries: int) -> Agent:
    return Agent(
        name="Assistant",
        instructions="你是助手，简洁回答问题。",
        model=model,
        model_settings=ModelSettings(
            temperature=0,
            timeout=timeout,
            # max_retries：单次调用失败（超时/5xx）后，SDK 自动重试几次；
            # backoff 可以配置重试间隔，避免立刻重打把网关打得更崩。
            retry=ModelRetrySettings(max_retries=max_retries),
        ),
    )


def demo_auto_retry() -> None:
    print("=== 1. 自动重试 ===")
    agent = build_agent(model=default_model(), timeout=20, max_retries=2)
    t0 = time.time()
    result = Runner.run_sync(agent, "用一句话介绍一下重试机制的作用。")
    print(result.final_output)
    print(f"(耗时 {time.time() - t0:.1f}s，这期间可能发生了0~2次自动重试)")


def demo_manual_fallback() -> None:
    print("\n=== 2. 手动降级：主模型不行就换备用模型 ===")
    # 真实项目里，"主模型"可能是能力更强但偶尔抽风的模型，"备用模型"是更朴素但更稳的模型。
    # 这里故意把主模型名写错（模拟"主模型/主服务不可用"），保证这个演示每次都会走到降级分支；
    # 实际项目中触发降级的通常是超时或 5xx，不会是模型名写错，但处理逻辑是一样的。
    primary = build_agent(model="hy4-does-not-exist", timeout=20, max_retries=0)
    fallback = build_agent(model="hy3", timeout=30, max_retries=1)

    question = "用一句话介绍一下你自己。"
    try:
        result = Runner.run_sync(primary, question)
        print(f"[主模型 hy4 成功] {result.final_output}")
    except Exception as e:
        # 降级分支要兜住的异常来源很杂：SDK 自己的 AgentsException（超时、模型拒答），
        # 也可能是底层 openai 客户端直接抛出的异常（鉴权失败、5xx）。
        # 生产代码可以按需只捕获特定类型，这里为了演示"怎么兜底"用了宽泛的 Exception。
        print(f"[主模型 hy4 失败: {type(e).__name__}] 降级到备用模型 hy3")
        result = Runner.run_sync(fallback, question)
        print(f"[备用模型 hy3 成功] {result.final_output}")


def main() -> None:
    demo_auto_retry()
    demo_manual_fallback()


if __name__ == "__main__":
    main()
