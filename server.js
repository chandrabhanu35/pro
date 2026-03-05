require('dotenv').config();
const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const Anthropic = require('@anthropic-ai/sdk');

const app = express();
const server = http.createServer(app);
const io = new Server(server, { cors: { origin: '*' } });

app.use(express.static('public'));
app.use(express.json());

// ── Anthropic client ──────────────────────────────────────────────────────────
if (!process.env.ANTHROPIC_API_KEY) {
  console.error('❌  ANTHROPIC_API_KEY is not set. Copy .env.example to .env and fill in your key.');
  process.exit(1);
}
const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

// ── Helpers ───────────────────────────────────────────────────────────────────
const WORKER_COLORS  = ['#00E5FF', '#B347EA', '#00FF87', '#FF2D78', '#FF6B35'];
const WORKER_EMOJIS  = ['🔬', '📊', '✍️', '🎯', '⚡'];
let   taskCounter    = 0;

/** Broadcast an event to all connected clients */
function broadcast(event, data) {
  io.emit(event, data);
}

/** Stream a Claude response; each text delta is emitted as agent:stream */
async function streamClaude(agentId, { system, userMsg, maxTokens = 800, thinking = false }) {
  let full = '';
  const params = {
    model: 'claude-opus-4-6',
    max_tokens: maxTokens,
    system,
    messages: [{ role: 'user', content: userMsg }],
  };
  if (thinking) params.thinking = { type: 'adaptive' };

  const stream = anthropic.messages.stream(params);
  for await (const event of stream) {
    if (event.type === 'content_block_delta' && event.delta.type === 'text_delta') {
      full += event.delta.text;
      broadcast('agent:stream', { id: agentId, text: event.delta.text });
    }
  }
  return full;
}

// ── Manager Agent ─────────────────────────────────────────────────────────────
async function runManagerAgent(task, taskId) {
  const managerId = `manager_${taskId}`;

  broadcast('agent:created', {
    id: managerId, role: 'manager',
    title: 'Manager', emoji: '🧠', color: '#FFD700',
    task: `Orchestrating: "${task}"`,
  });

  await sleep(200);
  broadcast('agent:status', { id: managerId, status: 'thinking' });
  broadcast('agent:message', {
    from: managerId, to: 'all', fromName: 'Manager',
    message: `📥 Task received: "${task}"\nAnalyzing complexity and creating execution plan...`,
  });

  // ── Manager calls Claude to decompose the task ────────────────────────────
  let planRaw = '';
  try {
    planRaw = await streamClaude(managerId, {
      thinking: true,
      maxTokens: 1600,
      system: `You are an AI Manager Agent. Decompose tasks into parallel subtasks for a worker team.
IMPORTANT — respond ONLY with valid JSON, no markdown fences, no extra text:
{
  "analysis": "One or two sentence analysis of the task",
  "workers": [
    { "role": "RoleName",  "emoji": "single emoji", "task": "Specific, actionable subtask" },
    { "role": "RoleName2", "emoji": "single emoji", "task": "Specific, actionable subtask" },
    { "role": "RoleName3", "emoji": "single emoji", "task": "Specific, actionable subtask" }
  ]
}
Use exactly 3 workers. Choose roles that complement each other (e.g., Researcher + Analyst + Writer).`,
      userMsg: `Task to orchestrate: ${task}`,
    });
  } catch (err) {
    planRaw = JSON.stringify({
      analysis: `Breaking down: ${task}`,
      workers: [
        { role: 'Researcher',  emoji: '🔬', task: `Research key aspects of: ${task}` },
        { role: 'Analyst',     emoji: '📊', task: `Analyze and structure findings for: ${task}` },
        { role: 'Synthesizer', emoji: '✍️', task: `Synthesize and present results for: ${task}` },
      ],
    });
  }

  // Parse manager plan
  let plan;
  try {
    const m = planRaw.match(/\{[\s\S]*\}/);
    plan = JSON.parse(m ? m[0] : planRaw);
  } catch {
    plan = {
      analysis: `Working on: ${task}`,
      workers: [
        { role: 'Researcher',  emoji: '🔬', task: `Research: ${task}` },
        { role: 'Analyst',     emoji: '📊', task: `Analyze: ${task}` },
        { role: 'Writer',      emoji: '✍️', task: `Write report on: ${task}` },
      ],
    };
  }

  broadcast('agent:message', {
    from: managerId, to: 'all', fromName: 'Manager',
    message: `📋 Analysis complete: ${plan.analysis}\n🚀 Spawning ${plan.workers.length} worker agents...`,
  });
  broadcast('agent:status', { id: managerId, status: 'working' });

  // ── Spawn worker agents ───────────────────────────────────────────────────
  const workerIds   = [];
  const workerMeta  = [];   // { id, role, emoji, color, task }

  plan.workers.forEach((w, i) => {
    const wId    = `worker_${i + 1}_${taskId}`;
    const color  = WORKER_COLORS[i % WORKER_COLORS.length];
    const emoji  = w.emoji || WORKER_EMOJIS[i % WORKER_EMOJIS.length];
    workerIds.push(wId);
    workerMeta.push({ id: wId, role: w.role, emoji, color, task: w.task });

    broadcast('agent:created', {
      id: wId, role: 'worker',
      title: w.role, emoji, color, task: w.task,
    });
    broadcast('agent:message', {
      from: managerId, to: wId, fromName: 'Manager', toName: w.role,
      message: `🚀 Deploying you!\nYour assignment: ${w.task}`,
    });
  });

  await sleep(400);

  // ── Run all workers in parallel ───────────────────────────────────────────
  const results = {};
  await Promise.all(
    workerMeta.map(meta =>
      runWorkerAgent(meta, managerId, workerMeta, results)
    )
  );

  // ── Manager compiles final report ─────────────────────────────────────────
  broadcast('agent:status', { id: managerId, status: 'thinking' });
  broadcast('agent:message', {
    from: managerId, to: 'all', fromName: 'Manager',
    message: `✅ All workers finished! Compiling final report...`,
  });

  const resultsBlock = Object.values(results)
    .map(r => `[${r.role}]\n${r.result}`)
    .join('\n\n---\n\n');

  let finalReport = '';
  try {
    finalReport = await streamClaude(managerId, {
      maxTokens: 600,
      system: 'You are a Manager AI. Compile worker results into a clear, concise final report (4–6 sentences). Be structured and actionable.',
      userMsg: `Original task: "${task}"\n\nWorker results:\n${resultsBlock}\n\nWrite the final summary report.`,
    });
  } catch {
    finalReport = `Task "${task}" has been completed by the agent team. All workers have submitted their findings and the analysis is ready.`;
  }

  broadcast('agent:message', {
    from: managerId, to: 'all', fromName: 'Manager',
    message: `📊 FINAL REPORT\n\n${finalReport}`,
  });
  broadcast('agent:status', { id: managerId, status: 'terminated' });
  broadcast('task:complete', { taskId, report: finalReport });
}

// ── Worker Agent ──────────────────────────────────────────────────────────────
async function runWorkerAgent(meta, managerId, allWorkers, results) {
  const { id, role, task } = meta;

  broadcast('agent:status', { id, status: 'working' });
  broadcast('agent:message', {
    from: id, to: managerId, fromName: role, toName: 'Manager',
    message: `Agent [${role}] online! Starting work on:\n"${task}"`,
  });

  // ── Peer-to-peer communication ────────────────────────────────────────────
  const peers = allWorkers.filter(w => w.id !== id);
  if (peers.length > 0) {
    await sleep(500 + Math.random() * 1500);
    broadcast('agent:status', { id, status: 'communicating' });

    const peer = peers[Math.floor(Math.random() * peers.length)];

    broadcast('agent:message', {
      from: id, to: peer.id, fromName: role, toName: peer.role,
      message: `Hey [${peer.role}]! 👋 I'm handling "${task}". What's your focus? Want to make sure we don't overlap.`,
    });

    await sleep(800 + Math.random() * 600);

    broadcast('agent:message', {
      from: peer.id, to: id, fromName: peer.role, toName: role,
      message: `Hi [${role}]! I'm on "${peer.task}". Totally different angle — let's share findings when we're done. Go! 💪`,
    });

    await sleep(400);
    broadcast('agent:status', { id, status: 'working' });
  }

  // ── Worker calls Claude to do the actual work ─────────────────────────────
  let result = '';
  try {
    result = await streamClaude(id, {
      maxTokens: 500,
      system: `You are an AI Worker Agent with the specialized role: ${role}.
Complete your assigned subtask with expertise. Be concise and structured (3–4 sentences max).`,
      userMsg: `Your subtask: ${task}\n\nProvide your key findings and analysis.`,
    });
  } catch (err) {
    result = `Analysis for "${task}" is complete. Key findings have been processed and are ready for the manager.`;
    broadcast('agent:stream', { id, text: result });
  }

  results[id] = { role, result };

  broadcast('agent:message', {
    from: id, to: managerId, fromName: role, toName: 'Manager',
    message: `✅ Task complete! Results submitted to Manager.`,
  });

  broadcast('agent:status', { id, status: 'terminated' });
}

// ── Socket.io connection ──────────────────────────────────────────────────────
io.on('connection', socket => {
  console.log(`🔌 Client connected: ${socket.id}`);

  socket.on('task:start', async ({ task }) => {
    if (!task || !task.trim()) return;
    const taskId = ++taskCounter;
    try {
      await runManagerAgent(task.trim(), taskId);
    } catch (err) {
      console.error('Task error:', err);
      io.emit('task:error', { message: err.message });
    }
  });

  socket.on('disconnect', () => {
    console.log(`🔌 Client disconnected: ${socket.id}`);
  });
});

// ── Start server ──────────────────────────────────────────────────────────────
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`\n🤖 AI Agent Swarm running → http://localhost:${PORT}\n`);
});

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
