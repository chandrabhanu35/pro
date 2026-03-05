# 🤖 AI Agent Swarm — Multi-Agent Orchestration System

A real-time website where a **Manager AI** dynamically creates **Worker AI agents**, assigns them parallel tasks, lets them **talk to each other**, and terminates them when the work is done — all visible in a live dashboard UI.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🧠 **Manager Agent** | Analyzes your task and decomposes it into parallel subtasks using Claude Opus 4.6 |
| 👷 **Worker Agents** | 3 specialized workers spawned dynamically (e.g., Researcher, Analyst, Writer) |
| ⚡ **Parallel Execution** | All workers run simultaneously via `Promise.all` |
| 💬 **Agent Communication** | Workers talk to each other and report back to the Manager |
| 📡 **Real-Time UI** | Live agent cards with streaming text, status indicators, and a message feed |
| 🔴 **Auto-Termination** | Each agent terminates after completing its task |
| 📊 **Final Report** | Manager compiles all worker results into a structured report |

---

## 🚀 Quick Start

### 1. Clone & Install
```bash
git clone <repo-url>
cd ai-agent-swarm
npm install
```

### 2. Configure API Key
```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
# Get one at: https://console.anthropic.com
```

### 3. Run
```bash
npm start
# Open http://localhost:3000
```

---

## 🏗️ Architecture

```
Browser (Socket.io client)
    │
    ▼
Express Server (server.js)
    │
    ├── Manager Agent  ──► Claude Opus 4.6 (task decomposition)
    │         │
    │    Spawns 3 Workers (in parallel)
    │         │
    ├── Worker 1 ──► Claude Opus 4.6 (subtask A)
    ├── Worker 2 ──► Claude Opus 4.6 (subtask B)  ← run simultaneously
    ├── Worker 3 ──► Claude Opus 4.6 (subtask C)
    │         │
    │    Results collected
    │         │
    └── Manager Agent  ──► Claude Opus 4.6 (compile final report)
```

All events are streamed to the browser via **Socket.io** in real-time.

---

## 🌐 Hosting Options

GitHub Pages only serves static files — for this Node.js app, use:

| Platform | Free Tier | Deploy |
|----------|-----------|--------|
| [Railway](https://railway.app) | ✅ | Connect GitHub repo → auto-deploy |
| [Render](https://render.com) | ✅ | New Web Service → connect repo |
| [Fly.io](https://fly.io) | ✅ | `fly launch` |

Set the `ANTHROPIC_API_KEY` environment variable in your hosting platform's dashboard.

---

## 🛠️ Tech Stack

- **Backend**: Node.js + Express + Socket.io
- **AI**: Anthropic Claude Opus 4.6 (`@anthropic-ai/sdk`)
- **Frontend**: Vanilla HTML/CSS/JavaScript (no framework)
- **Realtime**: Socket.io WebSockets

---

## 📂 Structure

```
├── server.js           # Backend: agents, Claude API, Socket.io
├── public/
│   ├── index.html      # UI markup
│   ├── style.css       # Dark theme with glassmorphism
│   └── client.js       # Socket.io client + dynamic UI
├── package.json
└── .env.example        # API key template
```
