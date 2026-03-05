# Claude Agents — Python Examples

A collection of agent examples built with the [Claude Agent SDK](https://pypi.org/project/claude-agent-sdk/).

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-api-key"
```

## Examples

### 1. `basic_agent.py` — Codebase Explorer
A simple agent that reads files in the current directory and summarises them.

```bash
python basic_agent.py
```

**Tools used:** `Read`, `Glob`, `Grep`

---

### 2. `tool_agent.py` — Custom Tool Agent
Demonstrates defining custom in-process tools (weather lookup, calculator) via an MCP server.

```bash
python tool_agent.py
```

**Tools used:** custom `get_weather`, custom `calculate`

---

### 3. `subagent_agent.py` — Orchestrator + Subagent
An orchestrator agent spawns a specialised `code-reviewer` subagent to review Python files.

```bash
python subagent_agent.py
```

**Tools used:** `Read`, `Glob`, `Grep`, `Agent` (spawns `code-reviewer` subagent)

---

### 4. `web_research_agent.py` — Web Research Agent
Searches the web and fetches pages to produce a research summary on a given topic.

```bash
python web_research_agent.py
```

**Tools used:** `WebSearch`, `WebFetch`

## Key Concepts

| Concept | Description |
|---|---|
| `query()` | Simple one-shot interface — returns an async iterator of messages |
| `ClaudeSDKClient` | Full-control interface — needed for custom tools and interruption |
| `ClaudeAgentOptions` | Configuration: tools, permissions, MCP servers, subagents, etc. |
| `AgentDefinition` | Defines a named subagent with its own prompt and tool set |
| `create_sdk_mcp_server` | Registers custom Python functions as tools via in-process MCP |
| `ResultMessage` | Final output message from the agent |
