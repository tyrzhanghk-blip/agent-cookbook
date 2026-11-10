# 案例13：会话持久化（Session）

## 学什么
- 案例4的"记忆"是手动拼 `to_input_list()`，历史存在 Python 变量里，进程一退出就没了，也没法支持多用户并发。
- `Session`（这里用内置的 `SQLiteSession`）把历史存到数据库：
  - `session_id`：区分"这是谁的对话"（可以是用户ID、会话ID）。
  - `db_path`：数据落在哪个 SQLite 文件（生产环境可以自己实现 `SessionABC` 接到 Redis/Postgres）。
  - 给 `Runner.run_sync(..., session=session)` 传入 session 后，**不用再手动拼历史**，SDK 自动读写。
- 这是从"能跑起来的脚本"走向"能部署的产品"的关键一步：历史要能跨进程、跨重启存在。

## 怎么运行
```bash
uv run python cases/case13_session_persistence/main.py
```
运行两次：第二次运行时，即使是全新进程，Assistant 依然能从数据库里读到"豆豆"这个历史。

## 预期输出
第一轮告知"豆豆"，第二轮能正确回答猫的名字叫豆豆。
数据库文件 `conversations.db` 会生成在本案例目录下（已加入 .gitignore，不提交到仓库）。

## 下一步
案例14讲模型调用的重试与降级策略——案例3里踩过的"网关偶发超时"就属于这一类问题。
