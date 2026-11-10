# 案例7：安全护栏（guardrails）

## 学什么
- `@input_guardrail` 装饰一个异步函数，在主 Agent 真正处理输入**之前**跑一遍检查。
- 护栏本身也可以是一个（轻量）Agent——用语义判断代替死板的关键词黑名单，更稳健。
- 返回 `GuardrailFunctionOutput(tripwire_triggered=True)` 会让 SDK 抛出 `InputGuardrailTripwireTriggered`，
  调用方 `try/except` 住它，决定怎么兜底（拒绝、转人工、返回固定话术……）。
- `output_guardrail` 原理相同，只是检查的是**模型产出之后**的内容（本案例未演示，用法对称）。

## 怎么运行
```bash
uv run python cases/case7_guardrails/main.py
```

## 预期输出
退款问题正常回答；写诗这种离题请求会被护栏拦截，打印拦截原因而不是走到主 Agent。

## 下一步
案例8讲可观测性（tracing）：怎么看懂 Agent 在后台做了什么。
