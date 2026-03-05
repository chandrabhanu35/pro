"""
Agent with custom tools using the Claude Agent SDK + MCP server.
Demonstrates defining and using custom tools via an in-process MCP server.
"""

import anyio
from claude_agent_sdk import (
    tool,
    create_sdk_mcp_server,
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
)


# --- Custom tool definitions ---

@tool(
    "get_weather",
    "Get the current weather for a city",
    {"city": str},
)
async def get_weather(args):
    city = args["city"]
    # Replace with a real weather API call in production
    return {
        "content": [
            {"type": "text", "text": f"The weather in {city} is 22°C and sunny."}
        ]
    }


@tool(
    "calculate",
    "Evaluate a simple arithmetic expression",
    {"expression": str},
)
async def calculate(args):
    expression = args["expression"]
    try:
        # Only allow safe arithmetic expressions
        allowed_chars = set("0123456789+-*/(). ")
        if not all(c in allowed_chars for c in expression):
            raise ValueError("Expression contains disallowed characters.")
        result = eval(expression, {"__builtins__": {}})  # noqa: S307
        return {"content": [{"type": "text", "text": str(result)}]}
    except Exception as exc:
        return {"content": [{"type": "text", "text": f"Error: {exc}"}]}


# --- Agent runner ---

async def run_agent(prompt: str) -> None:
    server = create_sdk_mcp_server(
        "custom-tools",
        tools=[get_weather, calculate],
    )

    options = ClaudeAgentOptions(
        mcp_servers={"tools": server},
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query(prompt)
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text, end="", flush=True)
    print()


async def main():
    print("=== Custom Tool Agent ===\n")

    await run_agent("What's the weather in Paris? Also, what is 123 * 456?")


if __name__ == "__main__":
    anyio.run(main)
