# 案例16：产品化界面 —— CLI 与 Web

## 学什么
前面15个案例都是"跑一个脚本看效果"，这个案例讲：**同一个 Agent，怎么套上真正能给人用的界面**。

核心思路是把 Agent 逻辑和界面彻底分开：
- `agent.py`：Agent 定义 + `reply(session_id, user_input) -> str`，这是唯一的业务入口。
- `cli.py`：终端界面，循环读 `input()`，调 `reply()`，打印结果。
- `web.py`：网页界面，用标准库 `http.server` 起一个极简 HTTP 服务（故意不用 FastAPI/Flask，避免这个案例的重点变成"怎么用某个 web 框架"），提供一个聊天页面 + `/api/chat` 接口，内部还是调同一个 `reply()`。

两种界面都复用案例13学到的 `SQLiteSession`：`reply()` 内部按 `session_id` 加载/保存历史，所以：
- CLI 里换个用户名，就是换一个独立的对话历史。
- Web 页面关掉浏览器重新打开，助手依然记得你刚才说过的话（因为 session_id 固定、历史在磁盘上）。

生产环境建议把 `web.py` 换成 FastAPI/Flask + 真正的用户登录态来生成 `session_id`，但 Agent 这一侧的调用方式完全不变——这正是"界面是壳子，Agent 是核心"的意义。

## 踩过的坑：event loop 冲突

最初 `agent.py` 提供的是一个同步 `reply()`，内部每次调用都 `asyncio.run(areply(...))`——
每次新建一个 event loop，用完就关掉。这在只调用一次时没问题，但第二次调用就会报：

```
RuntimeError: <asyncio.locks.Event object ...> is bound to a different event loop
```
或者
```
RuntimeError: Event loop is closed
```

原因：底层 `AsyncOpenAI` 客户端的连接池、锁/事件这些对象，在第一次请求时会绑定到当时所在的
event loop 上；`asyncio.run()` 结束时会把这个 loop 关掉，这些对象也就失效了。下一次调用
新建了另一个 loop，对象还绑定着已关闭的旧 loop，于是报错。

修复方式：**全程只用一个长期存在的 event loop**，所有 `areply()` 调用都丢进这同一个 loop：
- `cli.py`：在 `main()` 开头创建一个 `loop`，整个交互循环里都用 `loop.run_until_complete(areply(...))`，直到用户退出才 `loop.close()`。
- `web.py`：`ThreadingHTTPServer` 每个请求会开新线程，不能让每个线程各自跑一个新 loop。做法是单独起一个后台线程专门跑一个 loop（`loop.run_forever()`），所有请求线程都通过 `asyncio.run_coroutine_threadsafe(areply(...), loop)` 把协程丢进这个唯一的 loop 执行。

这也是"脚本"和"长期运行的服务"之间一个容易被忽略的差异：脚本里 `asyncio.run()` 调一次就退出，
怎么写都行；但服务要反复处理请求，event loop 的生命周期必须自己管好。

## 怎么运行

CLI：
```bash
uv run python cases/case16_interfaces/cli.py
```
会提示输入用户名作为 session_id，之后直接打字聊天，输入 `exit`/`quit` 退出。

Web：
```bash
uv run python cases/case16_interfaces/web.py
```
然后打开浏览器访问 http://127.0.0.1:8765 。

## 预期效果
- CLI：告诉助手你的名字后再问"我叫什么名字"，助手能正确回答；问"现在几点了"会触发 `get_current_time` 工具。
- Web：打开页面发消息，助手能记住上一条消息里的信息；关掉再打开页面（不重启 `web.py` 进程也不影响，因为历史在 SQLite 文件里）依然记得。

对话历史会存到本案例目录下的 `conversations.db`（已加入 `.gitignore`）。

## 整个教程走到这里
从案例0的"一个 Agent + 一次调用"，到这里已经有了：工具、上下文、记忆/持久化、多 Agent 协作（as_tool/handoff）、安全护栏、可观测性、流式输出、外部工具协议（MCP）、人工审批、重试降级、评估测试，最后套上能真正给人用的界面——这是一条从"学概念"到"能上线"的完整路径。