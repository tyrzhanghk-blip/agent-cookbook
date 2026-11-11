# 案例0：直连 OpenAI 基础接口（不经过 Agents SDK）

## 学什么
用 Agent 框架之前，先搞清楚最底层的 API 长什么样、网关通不通。本案例用 `openai`
客户端（Agents SDK 底层也是它，无需新依赖）直接测三个最基本的接口：

| 测试 | 接口 | 说明 |
|---|---|---|
| 1 | `GET /models` | 列出这个 key 能用的模型——排查"模型未授权"最直接的手段 |
| 2 | `POST /chat/completions` | 最经典的一次性对话（messages + finish_reason + usage） |
| 3 | `POST /chat/completions` + `stream=True` | 流式返回，"打字机效果"的底层原理（对比案例10的 SDK 级流式） |
| 4 | `POST /responses` | 新一代接口，**Agents SDK 默认走的就是它**（instructions + input、output_text、status） |
| 5 | `POST /responses` + `stream=True` | Responses 流式：与 chat 的纯文本 delta 不同，这是「事件流」（`response.output_text.delta` 等事件类型），案例10 过滤 reasoning 噪音的原理就在这 |
| 6 | 接口探测 | 自动对 models / chat / responses / embeddings / images / audio 等端点发探测请求，输出这个网关「支持哪些接口」的清单 |
| 7 | `POST /images/generations` | 文生图：从 /models 里找图像模型（名字含 image/dall/flux/sd），生成图片保存为 `generated_image.png`（支持 b64 和 URL 两种返回）；网关没有图像模型时会明确给出结论 |

## 排障价值
后续案例里会踩到的 `403 model not authorized`、`401 tracing` 报错，本质上都是这几个
底层接口的问题。本案例内置了一个现场演示：如果 `.env` 里的 `DEFAULT_MODEL` 不在
`/models` 返回的可用列表里（正是 403 的根源），会当场提示并自动改用第一个可用模型
继续测试——先查 /models 再选模型，就是最基本的排障顺序。

测试 6 的接口探测进一步回答"这个网关到底有哪些端点"——原理是看**状态码的类型**：
404 = 路由不存在（网关没实现）；400/401/403/422 = 路由存在，只是参数/权限/模型不对。
（一个歧义：有的网关对"模型不存在"也回 404，但 body 会写 model not found，代码里据此区分。）

## 怎么运行
```bash
uv run python cases/case0_openai_basics/main.py
```

复用 `.env` 的 `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `DEFAULT_MODEL`（与
`common/env.py` 同一套配置）；不设置 `OPENAI_BASE_URL` 就是官方 API。

**一个容易踩的坑**：`load_dotenv` 默认**不覆盖**已存在的环境变量——如果你的 shell 里
export 过 `OPENAI_BASE_URL`，`.env` 里的值会被静默忽略。本案例用
`load_dotenv(ENV_PATH, override=True)` 强制以 `.env` 为准，并在启动时打印
配置来源和读到的值，让"到底用的哪个 URL"一目了然。

## 预期输出
1. 打印配置来源（.env 路径）和读到的三个配置值；
2. 可用模型列表（如 hy3 / hy4），DEFAULT_MODEL 不可用时提示并自动纠正；
3. chat 基本对话返回回复 + finish_reason + token 用量；
4. chat 流式对话逐字打印；
5. responses 基本调用返回 output_text + status + token 用量，流式事件逐字打印；
6. 接口探测输出清单，例如：`GET /models [可用]`、`POST /chat/completions [存在]`、`POST /embeddings [不存在]`；
7. 文生图：网关有图像模型则保存 `generated_image.png`，没有则打印「该网关没有可用的图像模型」。

## 与其他案例的关系
- 后续所有案例都是通过 Agents SDK 间接调这些接口；本案例是"退到底层"看原始请求/响应，也是整套教程的第一个案例——先确认网关通、模型可用，再开始学 Agent。
- 案例10 的流式是 SDK 事件流（含 reasoning 等丰富事件），本案例测试 3 是最原始的
  chat completions delta 流，两者对照着看更容易理解 SDK 帮你做了什么。