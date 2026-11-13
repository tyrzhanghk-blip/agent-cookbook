# Agent Cookbook

一套基于 [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) 的 Agent 开发教程，通过循序渐进的案例帮助有编程基础、但没做过 Agent 开发的工程师掌握 Agent 开发的核心概念与工程实践。

## 环境准备

```bash
cp .env.example .env   # 填入 OPENAI_API_KEY，如走自定义网关还需填 OPENAI_BASE_URL / DEFAULT_MODEL
uv sync
```

每个案例都可以独立运行：

```bash
uv run python cases/<case_dir>/main.py
```

部分案例含测试，运行方式见各案例 README。

## 案例索引

| 编号 | 目录 | 主题 |
| --- | --- | --- |
| 0 | [case0_openai_basics](cases/case0_openai_basics) | 直连 OpenAI 基础接口：models / chat / 流式（SDK 之下的底层排障，建议最先跑） |
| 0 | [case0_skeleton](cases/case0_skeleton) | 最小可运行的 Agent + Runner 骨架 |
| 1 | [case1_instructions](cases/case1_instructions) | 动态 instructions（基于上下文生成系统提示） |
| 2 | [case2_tools_basic](cases/case2_tools_basic) | `@function_tool` 基础用法 |
| 3 | [case3_tools_advanced](cases/case3_tools_advanced) | 多工具协作 + 结构化输出（并记录了单 Agent 多职责的稳定性坑与拆分方案） |
| 4 | [case4_context_memory](cases/case4_context_memory) | context（业务数据） vs 对话历史的区分与使用 |
| 5 | [case5_agents_as_tools](cases/case5_agents_as_tools) | 用 `agent.as_tool` 把 Agent 组合成多专家协作 |
| 6 | [case6_handoff](cases/case6_handoff) | Agent 间的 handoff（移交控制权） |
| 7 | [case7_guardrails](cases/case7_guardrails) | 输入安全护栏（input guardrail） |
| 8 | [case8_tracing](cases/case8_tracing) | 自定义 TracingProcessor，接入可观测性 |
| 9 | [case9_project](cases/case9_project) | 综合小产品：订单客服工作台（整合前面所有能力） |
| 10 | [case10_streaming](cases/case10_streaming) | 流式输出（`Runner.run_streamed`） |
| 11 | [case11_mcp_tools](cases/case11_mcp_tools) | 通过 MCP（Model Context Protocol）接入外部工具 |
| 12 | [case12_human_approval](cases/case12_human_approval) | 人工审批流程（高风险工具调用的 human-in-the-loop） |
| 13 | [case13_session_persistence](cases/case13_session_persistence) | 会话持久化（`SQLiteSession`，跨进程保留对话历史） |
| 14 | [case14_retry_fallback](cases/case14_retry_fallback) | 重试与降级策略 |
| 15 | [case15_evaluation](cases/case15_evaluation) | 评估与测试（纯逻辑单测 + Agent 行为测试分层） |
| 16 | [case16_interfaces](cases/case16_interfaces) | 产品化界面：CLI 与 Web（复用同一个 Agent，界面只是壳子） |
| 17 | [case17_coding_agent](cases/case17_coding_agent) | 编程 Agent：Claude Code / Cursor 的最小复刻（沙盒内自主写码-运行-修复） |
| 18 | [case18_data_transform](cases/case18_data_transform) | 批量数据转换管道：杂乱工单 -> 严格 schema（部分成功/失败隔离/汇总报告） |
| 19 | [case19_agent_skills](cases/case19_agent_skills) | Agent Skills：领域知识写成 SKILL.md 按需加载（Claude Code Skill 机制复刻） |

## 学习建议

- 按编号顺序学习：0→9 是核心概念主线，10→15 是进阶与工程化主题，彼此相对独立，可按需跳读。
- 每个案例目录下的 README 会说明：这个案例要讲什么概念、关键代码片段、运行方法、以及（如果有）踩过的坑与解决方式。
- 走自定义网关（非官方 OpenAI API）时需要在 `.env` 配置 `OPENAI_BASE_URL` 与 `DEFAULT_MODEL`，详见 `common/env.py`。
