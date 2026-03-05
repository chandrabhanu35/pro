"""
Web research agent using the Claude Agent SDK.
Uses WebSearch and WebFetch to research a topic and summarise findings.
"""

import anyio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage


async def research(topic: str) -> str:
    result_text = ""
    async for message in query(
        prompt=f"Research the following topic and provide a concise summary with key facts: {topic}",
        options=ClaudeAgentOptions(
            allowed_tools=["WebSearch", "WebFetch"],
            max_turns=10,
        ),
    ):
        if isinstance(message, ResultMessage):
            result_text = message.result
    return result_text


async def main():
    print("=== Web Research Agent ===\n")

    topic = "Latest advances in quantum computing (2024-2025)"
    print(f"Researching: {topic}\n")

    summary = await research(topic)
    print(summary)


if __name__ == "__main__":
    anyio.run(main)
