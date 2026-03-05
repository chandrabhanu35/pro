"""
Basic agent example using the Claude Agent SDK.
Reads files and answers questions about a codebase.
"""

import anyio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage


async def main():
    print("=== Basic Codebase Explorer Agent ===\n")

    async for message in query(
        prompt="List the files in this directory and give a brief summary of what each one does.",
        options=ClaudeAgentOptions(
            cwd=".",
            allowed_tools=["Read", "Glob", "Grep"],
        ),
    ):
        if isinstance(message, ResultMessage):
            print(message.result)


if __name__ == "__main__":
    anyio.run(main)
