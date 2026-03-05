"""
Subagent example using the Claude Agent SDK.
An orchestrator agent spawns a specialised subagent to review code quality.
"""

import anyio
from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition, ResultMessage


async def main():
    print("=== Orchestrator + Code-Reviewer Subagent ===\n")

    async for message in query(
        prompt=(
            "Use the code-reviewer agent to review all Python files in the "
            "current directory and produce a brief quality report."
        ),
        options=ClaudeAgentOptions(
            cwd=".",
            allowed_tools=["Read", "Glob", "Grep", "Agent"],
            agents={
                "code-reviewer": AgentDefinition(
                    description="Expert Python code reviewer focused on quality, security, and best practices.",
                    prompt=(
                        "You are a senior Python engineer. Review the provided code for:\n"
                        "1. Correctness and logic errors\n"
                        "2. Security vulnerabilities\n"
                        "3. Style and readability (PEP 8)\n"
                        "4. Potential performance issues\n\n"
                        "Provide specific, actionable feedback with line numbers where relevant."
                    ),
                    tools=["Read", "Glob", "Grep"],
                )
            },
        ),
    ):
        if isinstance(message, ResultMessage):
            print(message.result)


if __name__ == "__main__":
    anyio.run(main)
