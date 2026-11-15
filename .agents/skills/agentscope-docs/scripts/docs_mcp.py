"""AgentScope 官方文档查询 CLI（仅标准库依赖）。

本模块的业务功能如下：
1. DocClient: 以 JSON-RPC 调用 AgentScope 文档站 MCP 服务（stateless Streamable HTTP）。
2. main: 命令行入口，提供 tools / search / tree / rg / cat / page 六个子命令。

用法：
    python -m scripts.docs_mcp tools
    python -m scripts.docs_mcp search "SOP 执行者 验证者" --language zh --version 2.0.9
    python -m scripts.docs_mcp tree /zh/versions/2.0.9/building-blocks -L 1
    python -m scripts.docs_mcp rg "tool_result_limit" /
    python -m scripts.docs_mcp cat /zh/versions/2.0.9/building-blocks/model/overview.mdx
    python -m scripts.docs_mcp page https://docs.agentscope.io/zh/versions/2.0.9/building-blocks/sop
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_MCP_URL = "https://docs.agentscope.io/mcp"
ACCEPT = "application/json, text/event-stream"
USER_AGENT = "agentscope-docs-skill/1.0"


def _http(url: str, *, data: bytes | None = None, headers: dict | None = None, timeout: float = 90.0) -> str:
    """发一次 HTTP 请求并返回 UTF-8 文本。

    Args:
        url: 目标地址。
        data: POST 请求体；None 表示 GET。
        headers: 附加请求头。
        timeout: 超时秒数。

    Returns:
        响应正文。

    Raises:
        urllib.error.URLError: 网络或 HTTP 状态错误。
    """
    all_headers = {"User-Agent": USER_AGENT}
    all_headers.update(headers or {})
    request = urllib.request.Request(url, data=data, headers=all_headers, method="POST" if data else "GET")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", "replace")


def _first_event(text: str) -> dict:
    """从 SSE 或纯 JSON 响应里取第一个 JSON-RPC 消息。"""
    for line in text.splitlines():
        if line.startswith("data:"):
            return json.loads(line[5:].strip())
    return json.loads(text)


class DocClient:
    """AgentScope 文档站 MCP 客户端。

    Attributes:
        url: MCP 端点地址。
        timeout: 单次请求超时秒数。
    """

    def __init__(self, url: str = DEFAULT_MCP_URL, timeout: float = 90.0) -> None:
        self.url = url
        self.timeout = timeout

    def _rpc(self, payload: dict) -> dict:
        """发送一条 JSON-RPC 消息。"""
        body = json.dumps(payload).encode("utf-8")
        text = _http(
            self.url,
            data=body,
            headers={"Content-Type": "application/json", "Accept": ACCEPT},
            timeout=self.timeout,
        )
        return _first_event(text)

    def call_tool(self, name: str, arguments: dict) -> str:
        """调用一个 MCP 工具并拼出文本结果。

        Args:
            name: 工具名。
            arguments: 工具入参。

        Returns:
            工具返回的文本内容。

        Raises:
            RuntimeError: 服务端返回 JSON-RPC 错误。
        """
        data = self._rpc(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            }
        )
        if "error" in data:
            raise RuntimeError(f"MCP 错误：{data['error']}")
        result = data.get("result", {})
        return "\n".join(
            item.get("text", "") for item in result.get("content", []) if item.get("type") == "text"
        )

    def list_tools(self) -> list[dict]:
        """列出服务端工具定义。"""
        data = self._rpc({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
        return data.get("result", {}).get("tools", [])

    def fs(self, command: str) -> str:
        """在文档虚拟文件系统上执行只读命令。"""
        return self.call_tool("query_docs_filesystem_agent_scope", {"command": command})

    def search(self, query: str, *, language: str | None, version: str | None) -> str:
        """语义检索站点内容。"""
        arguments: dict = {"query": query}
        if language:
            arguments["language"] = language
        if version:
            arguments["version"] = version
        return self.call_tool("search_agent_scope", arguments)

    def fetch_page(self, url: str) -> str:
        """直接抓取页面 Markdown。"""
        markdown = url if url.endswith((".md", ".mdx")) else url.rstrip("/") + ".md"
        return _http(markdown, timeout=self.timeout)


def _quote(text: str) -> str:
    """给虚拟文件系统命令里的参数加双引号。"""
    return '"' + text.replace('"', '\\"') + '"'


def build_parser() -> argparse.ArgumentParser:
    """构造命令行解析器。"""
    parser = argparse.ArgumentParser(prog="docs_mcp", description="AgentScope 文档查询（只读）")
    parser.add_argument(
        "--url",
        default=os.environ.get("AGENTSCOPE_DOCS_MCP", DEFAULT_MCP_URL),
        help="MCP 端点，默认取 AGENTSCOPE_DOCS_MCP 或官方地址",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("tools", help="列出 MCP 工具")

    p_search = sub.add_parser("search", help="语义检索文档")
    p_search.add_argument("query")
    p_search.add_argument("--language", default="zh", help="语言代码，默认 zh；传空串表示不限")
    p_search.add_argument("--version", default=None, help="版本过滤，如 2.0.9")

    p_tree = sub.add_parser("tree", help="列目录")
    p_tree.add_argument("path", nargs="?", default="/")
    p_tree.add_argument("-L", dest="depth", type=int, default=None, help="目录深度")

    p_rg = sub.add_parser("rg", help="全站按关键词/正则搜")
    p_rg.add_argument("pattern")
    p_rg.add_argument("path", nargs="?", default="/")
    p_rg.add_argument("-i", dest="ignore_case", action="store_true", help="忽略大小写")
    p_rg.add_argument("-l", dest="files_only", action="store_true", help="只列文件名")
    p_rg.add_argument("-C", dest="context", type=int, default=None, help="上下文行数")

    p_cat = sub.add_parser("cat", help="读整页")
    p_cat.add_argument("path")

    p_page = sub.add_parser("page", help="按 URL 抓 Markdown")
    p_page.add_argument("url")

    return parser


def main(argv: list[str] | None = None) -> int:
    """命令行入口。

    Args:
        argv: 参数列表；None 时取 sys.argv。

    Returns:
        进程退出码，0 表示成功。
    """
    sys.stdout.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    client = DocClient(url=args.url)

    if args.command == "tools":
        for tool in client.list_tools():
            print(f"{tool['name']}: {tool.get('description', '')[:160]}")
    elif args.command == "search":
        print(
            client.search(
                args.query,
                language=args.language or None,
                version=args.version,
            )
        )
    elif args.command == "tree":
        command = f"tree {_quote(args.path)}"
        if args.depth is not None:
            command += f" -L {args.depth}"
        print(client.fs(command))
    elif args.command == "rg":
        command = "rg"
        if args.ignore_case:
            command += " -i"
        if args.files_only:
            command += " -l"
        if args.context is not None:
            command += f" -C {args.context}"
        command += f" {_quote(args.pattern)} {_quote(args.path)}"
        print(client.fs(command))
    elif args.command == "cat":
        print(client.fs(f"cat {_quote(args.path)}"))
    elif args.command == "page":
        print(client.fetch_page(args.url))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
