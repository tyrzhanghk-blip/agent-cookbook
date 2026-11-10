# 案例0：骨架

## 学什么
- `Agent`：一个 agent 最少需要 `name` 和 `instructions` 两个参数。
- `Runner.run_sync`：同步执行一次 agent 对话，拿到 `result.final_output`。
- 这是后面所有案例的起点：先跑通，再逐步加能力（工具、上下文、多 agent、护栏……）。

## 怎么运行

```bash
uv run python cases/case0_skeleton/main.py
```

## 预期输出
Assistant 用一句话自我介绍（中文）。

## 下一步
案例1会讲 `instructions` 如何动态生成（而不是写死的字符串）。
