"""
案例16（Web 界面）：用 Python 标准库 http.server 搭一个最小聊天网页，
不引入 fastapi/flask 等新依赖——重点是演示"同一个 Agent 可以套不同的壳子"，
不是重点介绍某个 web 框架。

生产环境建议换成 FastAPI/Flask，但 Agent 调用方式（reply()）完全不变。
"""

import asyncio
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent import areply

# ThreadingHTTPServer 会给每个请求开一个新线程。如果每个线程各自 asyncio.run()，
# 底层 AsyncOpenAI 客户端内部的锁/事件会绑定到第一次用到的 event loop，
# 换一个线程/新 loop 再调用就会报 "bound to a different event loop"。
# 解决办法：全局只起一个 event loop（在专门的后台线程里跑），
# 所有请求都通过 run_coroutine_threadsafe 把协程扔进这个唯一的 loop 执行。
_loop = asyncio.new_event_loop()
threading.Thread(target=_loop.run_forever, daemon=True).start()


def reply(session_id: str, user_input: str) -> str:
    future = asyncio.run_coroutine_threadsafe(areply(session_id, user_input), _loop)
    return future.result()


HOST = "127.0.0.1"
PORT = 8765

PAGE = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8" />
<title>案例16：Agent 聊天网页</title>
<style>
  body { font-family: -apple-system, sans-serif; max-width: 640px; margin: 40px auto; padding: 0 16px; }
  #log { border: 1px solid #ddd; border-radius: 8px; padding: 12px; height: 360px; overflow-y: auto; margin-bottom: 12px; }
  .msg { margin: 6px 0; }
  .user { color: #0a58ca; }
  .bot { color: #198754; }
  form { display: flex; gap: 8px; }
  input[type=text] { flex: 1; padding: 8px; }
  button { padding: 8px 16px; }
</style>
</head>
<body>
  <h2>案例16：Agent 聊天网页</h2>
  <p style="color:#666">session_id 固定为 web_demo_user，关闭浏览器重开后历史依然保留（案例13 的 SQLiteSession）。</p>
  <div id="log"></div>
  <form id="form">
    <input type="text" id="input" placeholder="说点什么……" autocomplete="off" />
    <button type="submit">发送</button>
  </form>
<script>
const log = document.getElementById("log");
const form = document.getElementById("form");
const input = document.getElementById("input");

function append(role, text) {
  const div = document.createElement("div");
  div.className = "msg " + role;
  div.textContent = (role === "user" ? "你: " : "助手: ") + text;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  append("user", text);
  input.value = "";
  const resp = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text }),
  });
  const data = await resp.json();
  append("bot", data.reply);
});
</script>
</body>
</html>
"""

SESSION_ID = "web_demo_user"


class ChatHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):  # 安静一点，不打印默认访问日志
        pass

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            self._send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/api/chat":
            self._send(404, b"not found", "text/plain")
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            payload = json.loads(body)
            message = str(payload.get("message", "")).strip()
        except json.JSONDecodeError:
            message = ""

        if not message:
            self._send(400, json.dumps({"error": "message 不能为空"}).encode("utf-8"), "application/json")
            return

        answer = reply(SESSION_ID, message)
        self._send(200, json.dumps({"reply": answer}, ensure_ascii=False).encode("utf-8"), "application/json")

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), ChatHandler)
    print(f"打开浏览器访问 http://{HOST}:{PORT} 开始聊天（Ctrl+C 停止）")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()