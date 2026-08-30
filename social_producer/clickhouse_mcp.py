import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StdioConnectionParams,
)
from mcp import StdioServerParameters


env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)


clickhouse_mcp = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=["-m", "mcp_clickhouse.main"],
            env={
                **os.environ,
                "CLICKHOUSE_HOST": os.environ["CLICKHOUSE_HOST"],
                "CLICKHOUSE_PORT": os.environ["CLICKHOUSE_PORT"],
                "CLICKHOUSE_USER": os.environ["CLICKHOUSE_USER"],
                "CLICKHOUSE_PASSWORD": os.environ[
                    "CLICKHOUSE_PASSWORD"
                ],
                "CLICKHOUSE_DATABASE": os.environ[
                    "CLICKHOUSE_DATABASE"
                ],
                "CLICKHOUSE_SECURE": "true",
                "CLICKHOUSE_VERIFY": "true",
                "CLICKHOUSE_ALLOW_WRITE_ACCESS": "false",
                "CLICKHOUSE_MCP_SERVER_TRANSPORT": "stdio",
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