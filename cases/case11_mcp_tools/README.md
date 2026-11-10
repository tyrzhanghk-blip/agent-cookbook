# 案例11：MCP 工具接入

## 学什么
- **MCP（Model Context Protocol）**：一个标准化协议，用来描述"有哪些工具/资源可以给 Agent 用"。
  好处是**解耦**——工具的实现方（可以是任何语言、任何团队维护）和使用方（你的 Agent）只需要约定协议，不需要互相知道内部实现。
- `MCPServerStdio`：最常见的接入方式，通过子进程 + 标准输入输出跟 MCP 服务器通信。
  本案例自带一个最小的 MCP 服务器（`mcp_server.py`，用官方 `mcp` 包的 `MCPServer` 写的），暴露了 `search_faq` 和 `get_server_time` 两个工具。
- `Agent(mcp_servers=[...])`：和 `tools=[...]`（案例2/3的 `@function_tool`）是平行的两条路，二者可以同时使用——
  自己的业务逻辑用 `@function_tool`，接别人现成的能力（数据库、第三方API封装好的 MCP 服务）用 `mcp_servers`。
- 用 `async with` 管理 MCP 服务器的生命周期：进入时启动子进程并建立连接，退出时自动关闭。

## 怎么运行
```bash
uv run python cases/case11_mcp_tools/main.py
```
（不需要手动启动 `mcp_server.py`，`MCPServerStdio` 会自动把它拉起来当子进程。）

## 预期输出
Agent 通过 MCP 工具查到退货政策（7天无理由退货）和服务器当前时间。

## 下一步
案例12讲人工审批（human-in-the-loop）：某些工具调用需要人点头才能继续执行。
