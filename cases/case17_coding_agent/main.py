"""
案例17：编程 Agent —— 类似 Claude Code / Cursor 的最小复刻（CLI 交互版）
目标：给 Agent 配上"读写文件 + 执行命令"的工具，它就能在一个沙盒目录里
自主完成多步编程任务：看目录 -> 读/写代码 -> 跑测试 -> 看报错 -> 修复 -> 再跑。
这正是 Claude Code / Cursor 这类编程助手的核心循环，剩下的差异主要是
工具更丰富、上下文管理更精细、以及权限/安全控制更严格。

本案例是交互式的：在终端里输入任意编程任务（可以多轮追问、迭代修改），
像用 Claude Code 一样用这个迷你版。

安全提示：本案例把所有操作限制在 workspace/ 目录内（路径校验），
命令执行带超时。真实产品还需要更严格的权限模型（哪些命令要审批等，参考案例12）。
"""

import asyncio
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import Agent, ModelSettings, Runner, function_tool

from common.env import default_model, load_env

load_env()

# 沙盒目录：Agent 的一切文件操作都被限制在这里
WORKSPACE = Path(__file__).parent / "workspace"


def _safe_path(rel_path: str) -> Path:
    """把相对路径限制在 workspace 内，防止 ../ 逃逸到沙盒外面。"""
    p = (WORKSPACE / rel_path).resolve()
    if not p.is_relative_to(WORKSPACE):
        raise ValueError(f"路径 {rel_path} 超出了 workspace 范围")
    return p


# ---------- 工具：Agent 的"手" ----------

@function_tool
def list_files() -> str:
    """列出 workspace 目录下的所有文件（含子目录）。"""
    entries = [str(p.relative_to(WORKSPACE)) for p in sorted(WORKSPACE.rglob("*")) if not p.name.startswith(".")]
    print("  [工具] list_files")
    return "\n".join(entries) if entries else "（空目录）"


@function_tool
def read_file(path: str) -> str:
    """读取 workspace 内指定路径文件的内容。"""
    p = _safe_path(path)
    print(f"  [工具] read_file {path}")
    if not p.exists():
        return f"文件不存在: {path}"
    return p.read_text(encoding="utf-8")


@function_tool
def write_file(path: str, content: str) -> str:
    """把内容写入 workspace 内指定路径的文件（覆盖写，目录不存在会自动创建）。"""
    p = _safe_path(path)
    print(f"  [工具] write_file {path} ({len(content)} 字符)")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"已写入 {path}"


@function_tool
def run_command(command: str) -> str:
    """在 workspace 目录内执行一条 shell 命令（60秒超时），返回 stdout/stderr/退出码。"""
    print(f"  [工具] run_command: {command}")
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return "命令超时（60秒），被强制终止"
    output = proc.stdout
    if proc.stderr:
        output += f"\n[stderr]\n{proc.stderr}"
    output += f"\n[退出码 {proc.returncode}]"
    return output or "(无输出)"


# ---------- Agent：编程助手的"脑" ----------

coding_agent = Agent(
    name="CodingAgent",
    instructions=(
        "你是一个编程助手，在一个沙盒目录里完成任务。工作方式：\n"
        "1. 先用 list_files 了解目录现状，需要时 read_file 看已有代码；\n"
        "2. 用 write_file 写代码；\n"
        "3. 用 run_command 运行/测试（比如 python xxx.py），根据输出判断是否正确；\n"
        "4. 如果报错，读报错、改代码、再跑，直到通过——不要把验证工作留给用户。\n"
        "用户可能基于之前的结果继续提新要求，注意结合 workspace 里已有的文件。\n"
        "完成后，简要总结你做了什么、验证结果如何。"
    ),
    tools=[list_files, read_file, write_file, run_command],
    model=default_model(),
    model_settings=ModelSettings(temperature=0),
)

# 每轮对话带上历史（Agent 需要记得之前的任务和结果）
HISTORY: list = []


async def chat(user_input: str) -> str:
    """跑一轮：带历史调用 Agent，返回总结文本，并把新一轮写回历史。"""
    global HISTORY
    turn_input = HISTORY + [{"role": "user", "content": user_input}] if HISTORY else user_input
    # 编程任务往往要十几步工具调用，放宽轮数上限（默认10）
    result = await Runner.run(coding_agent, turn_input, max_turns=30)
    HISTORY = result.to_input_list()
    return result.final_output


def main() -> None:
    print(f"迷你编程 Agent（沙盒目录: {WORKSPACE}）")
    print("像 Claude Code 一样给它派活吧，例如：")
    print('  - "创建一个 calculator.py，实现加减乘除，除零抛 ValueError，写测试并跑通"')
    print('  - "给 calculator 再加一个 pow 函数，测试也要补上"')
    print("输入 exit / quit 退出。\n")

    # 案例16 踩过的坑：AsyncOpenAI 客户端绑定首次用到的 event loop，
    # 多轮对话必须全程共用同一个 loop，不能每轮 asyncio.run() 新建一个。
    loop = asyncio.new_event_loop()
    try:
        while True:
            try:
                user_input = input("你: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n再见！")
                break

            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit"}:
                print("再见！")
                break

            answer = loop.run_until_complete(chat(user_input))
            print(f"\nAgent: {answer}\n")
    finally:
        loop.close()


if __name__ == "__main__":
    main()
