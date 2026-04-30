import json
import os
from openai import AsyncOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from agent.prompts import SYSTEM_PROMPT

YANDEX_BASE_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1"
MODEL = f"gpt://{os.getenv('YANDEX_FOLDER_ID')}/{os.getenv('YANDEX_MODEL', 'yandexgpt-lite')}/latest"


def _build_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=os.getenv("YANDEX_API_KEY"),
        base_url=YANDEX_BASE_URL,
    )


async def _mcp_tools_and_session():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "mcp_server.server"],
    )
    return stdio_client(server_params)


async def run_agent(repo_url: str, question: str) -> str:
    async with stdio_client(
        StdioServerParameters(command="python", args=["-m", "mcp_server.server"])
    ) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools_response = await session.list_tools()
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.inputSchema,
                    },
                }
                for t in tools_response.tools
            ]

            client = _build_client()
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Repository: {repo_url}\n\nQuestion: {question}",
                },
            ]

            # agentic loop
            while True:
                response = await client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    max_tokens=4096,
                )
                choice = response.choices[0]
                messages.append(choice.message.model_dump(exclude_unset=False))

                if choice.finish_reason == "tool_calls":
                    for tool_call in choice.message.tool_calls:
                        args = json.loads(tool_call.function.arguments)
                        result = await session.call_tool(tool_call.function.name, args)
                        tool_text = result.content[0].text if result.content else ""
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": tool_text,
                        })
                else:
                    return choice.message.content or ""
