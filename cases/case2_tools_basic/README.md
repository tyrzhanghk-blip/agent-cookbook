# 案例2：工具（基础）

## 学什么
- `@function_tool` 把一个普通 Python 函数变成 Agent 能调用的工具。
- SDK 会自动读取函数签名 + docstring，生成工具的 JSON Schema 给模型看，所以**类型标注和 docstring 要写清楚**。
- Agent 拿到工具列表后，会自己判断"这个问题需不需要调用工具"。

## 怎么运行
```bash
uv run python cases/case2_tools_basic/main.py
```

## 预期输出
Agent 会先调用 `get_weather("北京")`，拿到"晴，18°C"后再组织语言回答。

## 下一步
案例3会加多个工具，并讲 `output_type`（让 Agent 输出结构化数据而不是一段文字）。
