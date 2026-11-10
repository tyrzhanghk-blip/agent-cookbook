# 案例10：流式输出（streaming）

## 学什么
- `Runner.run_streamed(agent, input)`：立刻返回，不等待模型生成完毕。
- `result.stream_events()`：异步迭代真正的内容增量。两种常见事件：
  - `RawResponsesStreamEvent`：最底层的增量。它的 `event.data.type` 有很多种（推理摘要、内容块变化等），
  **只有 `response.output_text.delta` 才是真正的最终回答正文**，拼起来适合做"打字机"效果。
  踩过的坑：不过滤 type 的话，会把模型的内部思考过程（reasoning）也当正文打印出来，这是不该展示给用户的。
  - `RunItemStreamEvent`：更高层的"事件"，比如一次工具调用结束、一条消息生成完毕，适合做"状态提示"（如"正在调用工具…"）。
- 和前面案例的 `Runner.run_sync` 相比：`run_sync` 要等全部生成完才返回，`run_streamed` 边生成边给。

## 怎么运行
```bash
uv run python cases/case10_streaming/main.py
```

## 预期输出
文字一个字一个字地打印出来（终端里能直观看到这个效果，而不是一次性蹦出一大段）。

## 下一步
案例11讲接入 MCP 工具生态；案例12讲人工审批（human-in-the-loop）。