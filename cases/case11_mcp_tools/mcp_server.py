"""
案例11的配套 MCP 服务器：一个最小的 stdio MCP Server，提供两个工具。
单独运行它没什么用——它是被 main.py 通过子进程拉起来、用 MCP 协议通信的。
"""

from mcp.server.mcpserver import MCPServer

server = MCPServer("knowledge-base")


@server.tool()
def search_faq(keyword: str) -> str:
    """在内部知识库里按关键词搜索 FAQ。"""
    fake_faq = {
        "退货": "支持7天无理由退货，商品需保持完好。",
        "运费": "订单满99元包邮，不满99元收取8元运费。",
        "会员": "会员享受生日当月9折优惠。",
    }
    for key, answer in fake_faq.items():
        if key in keyword:
            return answer
    return "没有找到相关 FAQ，建议转人工客服。"


@server.tool()
def get_server_time() -> str:
    """获取 MCP 服务器当前时间（用于演示：这是服务器侧的能力，不是客户端 Agent 自己算的）。"""
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    server.run(transport="stdio")
