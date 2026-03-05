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

---

## Autonomous Task Agents

Self-running agents that take a high-level goal and work autonomously until completion.
They plan, delegate to specialized sub-agents, handle dependencies, retry failures, and deliver results.

### Quick Start

```bash
# Interactive menu — pick an agent and describe your goal
python run_agents.py

# Or run directly from command line
python run_agents.py social "My fitness coaching business"
python run_agents.py app "A todo app with auth and cloud sync"
python run_agents.py money "I know Python and web development"
python run_agents.py website "A portfolio site for a photographer"
python run_agents.py custom "Any goal you can think of"
```

### 5. `task_engine.py` — Core Autonomous Engine

The brain of the system. Takes any goal, breaks it into subtasks using a planner agent,
assigns each subtask to a specialized agent (researcher, coder, content_creator, social_media,
business_strategist, designer, devops), runs them respecting dependencies, retries failures,
and produces a final summary.

```python
from task_engine import AutonomousTaskEngine
engine = AutonomousTaskEngine()
await engine.run("Build me a SaaS dashboard")
```

### 6. `social_media_agent.py` — Social Media Manager

Creates complete social media strategies: content calendars, ready-to-post content,
hashtag strategies, growth plans, and automation templates.

```bash
python social_media_agent.py "My bakery business"
```

### 7. `app_builder_agent.py` — App Builder

Builds complete applications — frontend, backend, database, auth, and deployment config.

```bash
python app_builder_agent.py "A recipe sharing app with user profiles"
```

### 8. `money_maker_agent.py` — Money Maker

Researches income opportunities, creates freelancing profiles, digital product templates,
and actionable plans to start earning.

```bash
python money_maker_agent.py "I know graphic design and video editing"
```

### 9. `website_builder_agent.py` — Website Builder

Builds complete, responsive, deployable websites with design systems, content, and deployment config.

```bash
python website_builder_agent.py "A landing page for a SaaS product"
```

### 10. `run_agents.py` — CLI Runner

Interactive menu or command-line interface to launch any autonomous agent.

```bash
python run_agents.py          # Interactive menu
python run_agents.py custom "Anything you want done"
```

---

## How Autonomous Agents Work

```
Your Goal
    │
    ▼
┌─────────────┐
│   Planner   │ ── Breaks goal into subtasks
│   Agent     │ ── Assigns specialized agents
└─────┬───────┘
      │
      ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Researcher  │  │   Coder     │  │  Designer   │
│   Agent     │  │   Agent     │  │   Agent     │
└─────┬───────┘  └─────┬───────┘  └─────┬───────┘
      │                │                │
      ▼                ▼                ▼
┌─────────────────────────────────────────────┐
│           Results & File Outputs            │
└─────────────────────────────────────────────┘
      │
      ▼
┌─────────────┐
│  Summary    │ ── What was done, files created, next steps
│   Agent     │
└─────────────┘
```

---

## Key Concepts

| Concept | Description |
|---|---|
| `query()` | Simple one-shot interface — returns an async iterator of messages |
| `ClaudeSDKClient` | Full-control interface — needed for custom tools and interruption |
| `ClaudeAgentOptions` | Configuration: tools, permissions, MCP servers, subagents, etc. |
| `AgentDefinition` | Defines a named subagent with its own prompt and tool set |
| `create_sdk_mcp_server` | Registers custom Python functions as tools via in-process MCP |
| `ResultMessage` | Final output message from the agent |
