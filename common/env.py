"""
各案例共用的环境加载逻辑：
- 从仓库根目录的 .env 读取 OPENAI_API_KEY
- 如果配置了 OPENAI_BASE_URL（比如公司内部网关），自动切到自定义端点
- 从 .env 读取 DEFAULT_MODEL（网关要求显式指定模型名时使用）
- 如果走的是非官方网关，默认关闭 OpenAI 官方 tracing 上报（网关 key 通常没有权限）
"""

import os
from pathlib import Path

from dotenv import load_dotenv


def load_env() -> None:
    root = Path(__file__).resolve().parent.parent
    load_dotenv(root / ".env")

    base_url = os.getenv("OPENAI_BASE_URL")
    if base_url:
        from agents import set_default_openai_client, set_tracing_disabled
        from openai import AsyncOpenAI

        # openai-agents 底层用的是 openai SDK 的 AsyncOpenAI client，
        # 通过设置默认 client 即可让所有 Agent 调用都走自定义端点。
        client = AsyncOpenAI(base_url=base_url, api_key=os.getenv("OPENAI_API_KEY"))
        set_default_openai_client(client)

        # 走第三方网关时，官方 tracing 后端通常无权限上报，关掉避免无意义的 401 警告。
        # 案例8会专门讲 tracing，到时候再按需打开/换成自建后端。
        set_tracing_disabled(True)


def default_model() -> str | None:
    """网关/第三方 key 通常要求显式指定模型名，从 .env 的 DEFAULT_MODEL 读取。"""
    return os.getenv("DEFAULT_MODEL")
