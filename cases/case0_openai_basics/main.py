"""
案例0：直连 OpenAI 基础接口（不经过 Agents SDK）
目标：在用 Agent 框架之前，先搞清楚最底层的 API 长什么样、网关通不通。
这个案例直接用 openai 客户端（Agents SDK 底层也是它）测两组、共五个基本接口：
  1. GET  /models            —— 列出这个 key 能用的模型（排查"模型未授权"最直接的手段）
  2. POST /chat/completions  —— 最经典的一次性对话
  3. POST /chat/completions + stream —— 流式返回（打字机效果的底层原理）
  4. POST /responses         —— 新一代接口（Agents SDK 默认走的就是它）
  5. POST /responses + stream —— Responses 的流式事件
  6. 接口探测                  —— 自动探测这个网关到底实现了哪些端点
  7. POST /images/generations —— 文生图（生成的图片保存为文件）

为什么值得单独学：前面所有案例的 403 model not authorized、401 tracing 报错，
本质上都是这几个底层接口的问题。会直连测试，排障就不用瞎猜。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import json
import os
import urllib.error
import urllib.request
from urllib.parse import urlparse

from dotenv import load_dotenv
from openai import OpenAI

# 显式从仓库根目录的 .env 读取配置。
# 注意 override=True：即使 shell 里已经 export 过同名变量，也以 .env 里的值为准——
# 否则 load_dotenv 默认不覆盖已存在的环境变量，你会读到 shell 的旧值而不自知。
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ENV_PATH, override=True)


def make_client() -> OpenAI:
    """用 .env 里的配置构造一个直连客户端。"""
    return OpenAI(
        base_url=os.getenv("OPENAI_BASE_URL") or None,  # 不设置就是官方 api.openai.com
        api_key=os.getenv("OPENAI_API_KEY"),
    )


def test_list_models(client: OpenAI) -> list[str]:
    """列出可用模型，返回模型 id 列表（失败返回空列表）。"""
    print("=" * 50)
    print("测试 1：GET /models —— 列出可用模型")
    try:
        models = client.models.list()
        ids = sorted(m.id for m in models.data)
        print(f"共 {len(ids)} 个模型：")
        for mid in ids:
            print(f"  - {mid}")
        return ids
    except Exception as e:
        print(f"[失败] {type(e).__name__}: {e}")
        return []


def test_chat(client: OpenAI, model: str) -> None:
    print("\n" + "=" * 50)
    print(f"测试 2：POST /chat/completions —— 基本对话（模型: {model}）")
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个简洁的助手，回答不超过20个字。"},
                {"role": "user", "content": "用一句话解释什么是API"},
            ],
        )
        msg = resp.choices[0].message
        print(f"回复: {msg.content}")
        print(f"finish_reason: {resp.choices[0].finish_reason}")
        if resp.usage:
            print(f"token 用量: prompt={resp.usage.prompt_tokens} completion={resp.usage.completion_tokens}")
    except Exception as e:
        print(f"[失败] {type(e).__name__}: {e}")


def test_chat_stream(client: OpenAI, model: str) -> None:
    print("\n" + "=" * 50)
    print(f"测试 3：POST /chat/completions + stream —— 流式返回（模型: {model}）")
    try:
        stream = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "从1数到10，逗号分隔"}],
            stream=True,
        )
        print("流式回复: ", end="", flush=True)
        for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                print(delta, end="", flush=True)
        print()  # 换行
    except Exception as e:
        print(f"\n[失败] {type(e).__name__}: {e}")


def test_responses(client: OpenAI, model: str) -> None:
    print("\n" + "=" * 50)
    print(f"测试 4：POST /responses —— 新一代接口（模型: {model}）")
    print("（Agents SDK 默认用的就是它：内置工具、多轮状态、reasoning 都从这里来）")
    try:
        resp = client.responses.create(
            model=model,
            instructions="你是一个简洁的助手，回答不超过20个字。",
            input="用一句话解释什么是Agent",
        )
        # output_text 是把 output 列表里的文本拼好的便捷属性
        print(f"回复: {resp.output_text}")
        print(f"status: {resp.status}")
        if resp.usage:
            print(f"token 用量: input={resp.usage.input_tokens} output={resp.usage.output_tokens}")
    except Exception as e:
        print(f"[失败] {type(e).__name__}: {e}")


def test_responses_stream(client: OpenAI, model: str) -> None:
    print("\n" + "=" * 50)
    print(f"测试 5：POST /responses + stream —— 流式事件（模型: {model}）")
    print("（对比测试3：Responses 的流是「事件流」，会告诉你在推理还是输出正文）")
    try:
        stream = client.responses.create(
            model=model,
            input="从1数到10，逗号分隔",
            stream=True,
        )
        print("流式回复: ", end="", flush=True)
        for event in stream:
            # 事件类型很多（created/response.in_progress/response.output_item.added/...），
            # 这里只取正文增量，与案例10 SDK 级流式的做法一致
            if event.type == "response.output_text.delta":
                print(event.delta, end="", flush=True)
        print()
    except Exception as e:
        print(f"\n[失败] {type(e).__name__}: {e}")


def test_image_generation(client: OpenAI, model: str, available: list[str]) -> None:
    print("\n" + "=" * 50)
    print("测试 7：POST /images/generations —— 文生图")
    # 图像模型和聊天模型通常不是同一个名字（官方是 gpt-image-1 / dall-e-3），
    # 先从 /models 列表里找名字带 image/dall/flux/sd 的候选，找不到再用聊天模型试一试。
    candidates = [m for m in available if any(k in m.lower() for k in ("image", "dall", "flux", "sd"))]
    candidates += [model]
    for img_model in candidates:
        print(f"尝试模型: {img_model}")
        try:
            resp = client.images.generate(
                model=img_model,
                prompt="一只戴墨镜的橘猫，像素风",
                size="1024x1024",
            )
            item = resp.data[0]
            out_path = Path(__file__).parent / "generated_image.png"
            if getattr(item, "b64_json", None):
                # b64 返回：直接落盘
                import base64
                out_path.write_bytes(base64.b64decode(item.b64_json))
                print(f"已保存图片: {out_path}")
            elif getattr(item, "url", None):
                # URL 返回：下载后落盘
                req = urllib.request.Request(item.url)
                with urllib.request.urlopen(req, timeout=30) as r:
                    out_path.write_bytes(r.read())
                print(f"已下载图片: {out_path}")
            return
        except Exception as e:
            print(f"  [失败] {type(e).__name__}: {e}")
    print("\n结论：该网关没有可用的图像模型（/images 路由可能存在，但没有模型能出图）。")


# ---------- 接口探测：这个网关到底有哪些端点？ ----------
#
# 原理：看状态码的"类型"，而不是只看成败。
#   404            -> 路由不存在，网关没实现这个接口
#   400/401/403/422 -> 接口存在！只是参数/权限/模型不对（路由认识才会走到参数校验）
#   200            -> 直接可用
# 注意一个歧义：有的网关对"模型不存在"也返回 404，但 body 里会写 model not found——
# 这种 404 说明路由是存在的，只是模型名不对。

# 要探测的端点：方法 + 路径 + 最小请求体（故意用不存在的模型名，避免真的消耗 token）
PROBE_TARGETS = [
    ("GET",  "/models",             None),
    ("POST", "/chat/completions",   {"model": "probe-not-a-model", "messages": []}),
    ("POST", "/responses",          {"model": "probe-not-a-model", "input": "hi"}),
    ("POST", "/embeddings",         {"model": "probe-not-a-model", "input": "hi"}),
    ("POST", "/images/generations", {"model": "probe-not-a-model", "prompt": "hi"}),
    ("POST", "/audio/speech",       {"model": "probe-not-a-model", "input": "hi"}),
]


def probe_endpoints(base_url: str, api_key: str) -> None:
    """对一组端点逐个发探测请求，按状态码判断网关是否实现了该接口。"""
    print("测试 6：接口探测 —— 这个网关实现了哪些端点？")
    print(f"目标: {base_url}\n")

    for method, path, body in PROBE_TARGETS:
        url = base_url.rstrip("/") + path
        req = urllib.request.Request(
            url,
            method=method,
            data=json.dumps(body).encode() if body else None,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                # 能到这一步就是 2xx，直接可用（探测用非法模型名一般不会走到这）
                print(f"  [可用   ] {method:4} {path}  (HTTP {resp.status})")
        except urllib.error.HTTPError as e:
            err_body = ""
            try:
                err_body = e.read().decode(errors="replace")[:200].lower()
            except Exception:
                pass
            if e.code == 404 and "model" not in err_body:
                print(f"  [不存在 ] {method:4} {path}  (HTTP 404，路由都没有)")
            else:
                why = "模型/参数不对" if "model" in err_body else "存在但被拒绝（权限/参数）"
                print(f"  [存在   ] {method:4} {path}  (HTTP {e.code}，{why})")
        except Exception as e:
            print(f"  [网络错误] {method:4} {path}  ({type(e).__name__}: {e})")

    print("\n判读：[存在/可用] 的接口可以想办法调通；[不存在] 的接口这个网关没实现，")
    print("换网关或改用其他方式（比如没有 /models 就只能问维护方要模型清单）。")


def main() -> None:
    print(f"配置来源: {ENV_PATH}")
    print(f"  OPENAI_BASE_URL = {os.getenv('OPENAI_BASE_URL') or '（未设置，走官方 api.openai.com）'}")
    print(f"  DEFAULT_MODEL   = {os.getenv('DEFAULT_MODEL') or '（未设置）'}")
    print(f"  OPENAI_API_KEY  = {(os.getenv('OPENAI_API_KEY') or '')[:8]}...\n")

    client = make_client()
    base = os.getenv("OPENAI_BASE_URL")
    print(f"目标 API: {base or 'https://api.openai.com/v1（官方默认）'}\n")

    # 模型列表测试在前：它就是"这个 key 到底能用什么模型"的权威答案
    available = test_list_models(client)

    model = os.getenv("DEFAULT_MODEL")
    if model and available and model not in available:
        # 这就是后续案例里 403 model not authorized 的根源，这里当场演示怎么发现和修复
        fixed = available[0]
        print(f"\n[注意] DEFAULT_MODEL={model} 不在可用列表里（会 403），自动改用 {fixed} 继续测试")
        model = fixed
    if not model:
        model = available[0] if available else None
    if not model:
        print("\n拿不到任何可用模型，跳过对话测试（检查 OPENAI_API_KEY / 网关地址）")
        return

    test_chat(client, model)
    test_chat_stream(client, model)
    test_responses(client, model)
    test_responses_stream(client, model)

    test_image_generation(client, model, available)

    print("\n" + "=" * 50)
    base_url = os.getenv("OPENAI_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY") or ""
    if base_url:
        probe_endpoints(base_url, api_key)
    else:
        print("（未设置 OPENAI_BASE_URL，跳过接口探测——官方 API 全部端点都有）")

    print("\n" + "=" * 50)
    print("小结：models / chat(+stream) / responses(+stream) 五个基础接口测完，探测了端点支持，并尝试了文生图。")
    print("Agents SDK 里发生的 403/401/超时问题，可以先回到这里定位是网关问题还是用法问题。")


if __name__ == "__main__":
    main()