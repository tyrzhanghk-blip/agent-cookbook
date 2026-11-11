# 案例17：编程 Agent —— 类似 Claude Code / Cursor 的最小复刻（CLI 交互）

## 学什么
Claude Code / Cursor 这类编程助手的本质，是一个**带工具的 Agent 循环**：

```
看目录/读代码 -> 写代码 -> 跑命令 -> 读报错 -> 改代码 -> 再跑 -> ... 直到完成
```

用前面案例学的知识就能复刻一个最小版本，只需要四个工具：

| 工具 | 作用 | 对应 Claude Code / Cursor 里的 |
|---|---|---|
| `list_files` | 列目录 | 文件树浏览 |
| `read_file` | 读文件 | 打开/引用代码 |
| `write_file` | 写文件 | 编辑器 Apply |
| `run_command` | 执行 shell 命令 | 终端 |

再配上一个"先看、再写、必须自己跑通验证"的 instructions，Agent 就能自主完成多步编程任务。
SDK 内部会自动跑"模型 <-> 工具"的循环（每次工具结果回传给模型决定下一步），`Runner.run(..., max_turns=30)` 放宽了轮数上限以适应十几步的编程任务。

**注意 max_turns 是 Runner.run 的参数，不是 Agent 的**——放在 Agent 构造里会直接报 TypeError。

## 交互设计
像 Claude Code 一样是 **CLI 交互式**的，不是固定跑某个演示任务：
- 每轮 `input()` 读你的任意任务，Agent 在沙盒里干完活并总结；
- 历史会带进下一轮（`result.to_input_list()`），所以可以迭代式提需求："再加个函数"、"把刚才那个改成……"；
- 每一步工具调用实时打印，能看到"思考-行动-观察"的完整轨迹；
- event loop 复用案例16的教训：整个会话共用一个 loop（`loop.run_until_complete`），避免 AsyncOpenAI 客户端跨 loop 报错。

## 安全设计
- **沙盒**：所有文件操作通过 `_safe_path()` 限制在 `workspace/` 目录内，`../` 逃逸会被拒绝。
- **超时**：`run_command` 带 60 秒超时，防止 Agent 起一个死循环命令拖住进程。
- 真实产品还需要：命令白名单/黑名单、危险操作人工审批（参考案例12的 `needs_approval`）、diff 预览确认等。

## 怎么运行
```bash
uv run python cases/case17_coding_agent/main.py
``}

试几轮（顺序体验"迭代式开发"）：
1. `创建一个 calculator.py，实现加减乘除，除零抛 ValueError，写测试并跑通`
2. `给 calculator 再加一个 pow 函数，测试也要补上`
3. `把测试换成 pytest 风格重写，用 pytest 跑通`

输入 `exit` / `quit` 退出。

## 预期效果
每轮任务 Agent 会自主完成"看现状 -> 写代码 -> 运行验证（不通过就修复重跑）-> 总结"；
第二轮起它会先读上一轮的文件再动手改。产物落在 `workspace/`（已 gitignore，
想从干净状态开始，删掉该目录里的产物即可）。

## 与真实产品的差距
- 上下文管理：真实代码库很大，需要检索/索引（embedding、代码图谱）而不是全量读文件。
- 工具更丰富：搜索、diff 编辑、LSP、git 操作等。
- 权限模型：哪些操作要用户确认、哪些可以自动执行。
- 流式输出与中断：参考案例10。

但核心循环是一样的——理解了本案例，就理解了这类产品的工作原理。
