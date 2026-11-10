# 案例15：评估与测试

## 学什么
给 Agent 写回归测试，分两层：

### 第一层：纯逻辑测试（`test_core_logic.py`）
把工具函数背后的业务逻辑（`calc_shipping_fee`）和 `@function_tool` 包装解耦开。
纯 Python 函数，不碰模型，秒级运行，**每次改代码都该跑**。

### 第二层：Agent 行为测试（`test_agent_behavior.py`）
真正调用模型，但断言的是**行为/结构**，不是死板的文字：
- 该不该调用工具、工具结果有没有体现在最终回答里（断言数字"8"而不是断言某句话）
- `output_type` 的结构化字段是否正确（断言 `isinstance` 和字段值，不断言措辞）
- 该不该被 guardrail 拦截——**也要测"正常问题没被误拦"**，不然光测"拦住了"容易把护栏调得太敏感

这一层标了 `@pytest.mark.llm`（见 `pyproject.toml` 的 marker 配置），慢、吃 token，
适合"改了 prompt / 加了工具之后"手动跑一遍，不建议每次 commit 都跑。

## 怎么运行
```bash
# 只跑快的（纯逻辑层，适合每次改代码都跑）
uv run pytest cases/case15_evaluation/test_core_logic.py -v

# 跑慢的（Agent 行为层，改完 prompt 后手动跑）
uv run pytest cases/case15_evaluation/test_agent_behavior.py -v

# 全部一起跑
uv run pytest cases/case15_evaluation/ -v
```

## 预期输出
9 个测试全部通过（4个纯逻辑 + 5个 Agent 行为）。

## 关键坑
`core.py` 在被 import 的时候就会创建 Agent（用到 `default_model()`），
所以 `load_env()` 必须在 `core.py` **内部**调用，不能依赖"调用方记得在 import 我之前先加载 .env"——
这种跨文件的顺序假设很容易在重构时悄悄被打破。
