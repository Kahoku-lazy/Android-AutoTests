from agentscope.mcp import MCPClient, StdioMCPConfig
from agentscope.tool import Toolkit

client = MCPClient(
    name="filesystem",
    is_stateful=True,
    mcp_config=StdioMCPConfig(
        command="mcp-server-filesystem",
        args=["--root", "/my/project"],
    ),
)

await client.connect()

toolkit = Toolkit(mcps=[client])

from agentscope.mcp import HttpMCPConfig, MCPClient
from agentscope.tool import Toolkit

client = MCPClient(
    name="weather",
    is_stateful=True,
    mcp_config=HttpMCPConfig(
        url="https://api.weather.com/mcp",
        headers={"Authorization": "Bearer xxx"},
    ),
)

await client.connect()

toolkit = Toolkit(mcps=[client])


from agentscope.mcp import MCPClient, StdioMCPConfig
from agentscope.tool import Toolkit

client = MCPClient(
    name="filesystem",
    is_stateful=True,
    mcp_config=StdioMCPConfig(
        command="mcp-server-filesystem",
        args=["--root", "/my/project"],
    ),
)

await client.connect()

toolkit = Toolkit(mcps=[client])
