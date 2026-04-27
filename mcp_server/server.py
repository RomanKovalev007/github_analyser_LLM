import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from mcp_server.tools.github import (
    get_repo_structure,
    read_file,
    search_files,
    get_readme,
)

server = Server("github-analyzer")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_repo_structure",
            description="Get the file and folder tree of a GitHub repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_url": {
                        "type": "string",
                        "description": "GitHub repository URL, e.g. https://github.com/owner/repo",
                    }
                },
                "required": ["repo_url"],
            },
        ),
        types.Tool(
            name="read_file",
            description="Read the contents of a specific file in a GitHub repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_url": {"type": "string"},
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file relative to the repo root",
                    },
                },
                "required": ["repo_url", "file_path"],
            },
        ),
        types.Tool(
            name="search_files",
            description="Search for files by name pattern or extension in a GitHub repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_url": {"type": "string"},
                    "pattern": {
                        "type": "string",
                        "description": "Substring to search for in file names, e.g. 'handler', '.go', 'auth'",
                    },
                },
                "required": ["repo_url", "pattern"],
            },
        ),
        types.Tool(
            name="get_readme",
            description="Get the README file of a GitHub repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_url": {"type": "string"},
                },
                "required": ["repo_url"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    handlers = {
        "get_repo_structure": get_repo_structure,
        "read_file": read_file,
        "search_files": search_files,
        "get_readme": get_readme,
    }
    if name not in handlers:
        raise ValueError(f"Unknown tool: {name}")

    result = await handlers[name](**arguments)
    return [types.TextContent(type="text", text=result)]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
