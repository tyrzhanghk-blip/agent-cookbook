# 案例8：可观测性（tracing）

## 学什么
- SDK 内部用 **trace**（一次完整的 `Runner.run`）和 **span**（trace 里的子步骤，比如一次 LLM 调用、一次工具调用）组织执行过程。
- 默认这些数据会上报到 OpenAI 官方 tracing 后端——但很多公司内部网关的 key 没有权限访问它（案例0里我们已经在 `common/env.py` 里默认关掉了这个上报，避免看到 401 警告）。
- 真正想"看见" Agent 在干什么，可以实现自己的 `TracingProcessor`，通过 `add_trace_processor()` 接入——
  打印到终端只是最简单的演示，生产环境可以换成写文件、发消息队列、接 APM。

## 怎么运行
```bash
uv run python cases/case8_tracing/main.py
```

## 预期输出
能看到 trace 开始/结束、每个 span（LLM 调用、工具调用）开始/结束的日志，最后是算术结果 42。

## 下一步
案例9：把前面学到的全部能力（工具、上下文、多专家、handoff、护栏、可观测性）整合成一个真实的小产品。
