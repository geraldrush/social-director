import os

from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters


clickhouse_mcp = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="/home/gery/.local/bin/uv",
            args=[
                "run",
                "--with",
                "mcp-clickhouse",
                "--python",
                "3.10",
                "mcp-clickhouse",
            ],
            env={
                **os.environ,
                "CLICKHOUSE_HOST": os.environ["CLICKHOUSE_HOST"],
                "CLICKHOUSE_PORT": os.environ["CLICKHOUSE_PORT"],
                "CLICKHOUSE_USER": os.environ["CLICKHOUSE_USER"],
                "CLICKHOUSE_PASSWORD": os.environ["CLICKHOUSE_PASSWORD"],
                "CLICKHOUSE_DATABASE": os.environ["CLICKHOUSE_DATABASE"],
                "CLICKHOUSE_SECURE": "false",
                "CLICKHOUSE_VERIFY": "false",
                "CLICKHOUSE_ALLOW_WRITE_ACCESS": "false",
            },
        ),
        timeout=120.0,
    ),
    tool_filter=[
        "list_databases",
        "list_tables",
        "run_query",
    ],
)


mcp_test_agent = Agent(
    name="mcp_test_agent",
    model="gemini-3.5-flash",
    description="Temporary agent used to verify ClickHouse MCP connectivity.",
    instruction="""
You are a read-only ClickHouse MCP test agent.

You have exactly these ClickHouse tools available:

- list_databases
- list_tables
- run_query

When the user asks about database contents, use these tools.

Do not invent tool names.
Do not invent database results.
Do not attempt writes.

For a specific campaign or content item, use run_query.
""",
    tools=[
        clickhouse_mcp,
    ],
)