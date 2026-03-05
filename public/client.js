/* ── AI Agent Swarm — Frontend ─────────────────────────────────────────────── */

const socket = io();

// ── State ─────────────────────────────────────────────────────────────────────
const agentMeta  = new Map();   // id → { color, role, title }
let   msgCount   = 0;
let   workerIdx  = 0;

const WORKER_COLORS = ['#00e5ff', '#b347ea', '#00ff87', '#ff2d78', '#ff6b35'];

// ── DOM refs ──────────────────────────────────────────────────────────────────
const $        = id => document.getElementById(id);
const grid     = $('agentsGrid');
const feedList = $('feedList');
const startBtn = $('startBtn');
const taskIn   = $('taskInput');

// ── Utilities ─────────────────────────────────────────────────────────────────
function esc(s) {
  return String(s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function now() {
  return new Date().toLocaleTimeString('en', { hour12:false, hour:'2-digit', minute:'2-digit', second:'2-digit' });
}
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ── Fill example task ─────────────────────────────────────────────────────────
window.fillTask = btn => { taskIn.value = btn.textContent.trim(); taskIn.focus(); };

// ── Start task ────────────────────────────────────────────────────────────────
function startTask() {
  const task = taskIn.value.trim();
  if (!task) { taskIn.focus(); return; }

  resetUI();

  startBtn.disabled = true;
  startBtn.querySelector('.btn-label').textContent = 'Running…';

  socket.emit('task:start', { task });
}

taskIn.addEventListener('keydown', e => {
  if (e.key === 'Enter') { e.preventDefault(); startTask(); }
});
startBtn.addEventListener('click', startTask);

// ── Reset ─────────────────────────────────────────────────────────────────────
function resetUI() {
  grid.innerHTML = `
    <div class="empty-state" id="emptyState">
      <div class="empty-emoji">🤖</div>
      <p class="empty-h">Spawning agents…</p>
      <p class="empty-p">Stand by while the swarm initialises</p>
    </div>`;
  feedList.innerHTML = `
    <div class="feed-empty">
      <div class="feed-empty-icon">💬</div>
      <p>Agent messages appear here in real-time</p>
    </div>`;
  agentMeta.clear();
  msgCount   = 0;
  workerIdx  = 0;
  $('agentCount').textContent = '0 Agents';
  $('msgCount').textContent   = '0 msgs';
  $('reportOverlay').style.display = 'none';
}

// ── Agent card creation ───────────────────────────────────────────────────────
function createCard({ id, role, title, emoji, color, task }) {
  const card = document.createElement('div');
  card.className   = `agent-card role-${role}`;
  card.id          = `card-${id}`;
  card.dataset.active = 'true';
  card.style.setProperty('--ac', color);

  card.innerHTML = `
    <div class="card-hdr">
      <div class="card-identity">
        <span class="card-emoji">${emoji}</span>
        <div>
          <div class="card-name" style="color:${color}">
            ${esc(title)}
            <span class="card-role-tag"
              style="background:${color}22;color:${color}">${role.toUpperCase()}</span>
          </div>
          <div class="card-id">${esc(id)}</div>
        </div>
      </div>
      <div class="card-status">
        <div class="status-dot created" id="dot-${id}"></div>
        <span class="status-lbl" id="lbl-${id}">Created</span>
      </div>
    </div>
    <div class="card-terminal" id="term-${id}">
      <div class="t-line"><span class="t-prompt">▸</span><span>Agent initialising…<span class="t-cursor"></span></span></div>
    </div>
    <div class="card-task">📌 <span>${esc(task)}</span></div>`;

  return card;
}

// ── Update agent status ───────────────────────────────────────────────────────
function setStatus(id, status) {
  const dot  = $(`dot-${id}`);
  const lbl  = $(`lbl-${id}`);
  const card = $(`card-${id}`);
  if (!dot) return;

  dot.className = `status-dot ${status}`;
  lbl.textContent = status.charAt(0).toUpperCase() + status.slice(1);

  const colors = {
    thinking:     '#f59e0b',
    working:      '#3b82f6',
    communicating:'#10b981',
    terminated:   '#ef4444',
    created:      '#4b5563',
  };
  dot.style.background = colors[status] || '#4b5563';
  dot.style.boxShadow  = ['terminated','created'].includes(status)
    ? 'none' : `0 0 8px ${colors[status]}`;

  if (status === 'terminated') {
    card?.classList.add('terminated');
    card?.setAttribute('data-active','false');
  } else {
    card?.setAttribute('data-active','true');
  }
}

// ── Stream text to terminal ───────────────────────────────────────────────────
function streamText(id, text) {
  const term = $(`term-${id}`);
  if (!term) return;

  let line = term.querySelector('.stream-line');
  if (!line) {
    // Remove init cursor
    term.querySelector('.t-cursor')?.remove();
    line = document.createElement('div');
    line.className = 't-line stream-line';
    line.innerHTML = `<span class="t-prompt" style="color:var(--cyan);opacity:.4">◈</span><span class="stext"></span>`;
    term.appendChild(line);
  }
  line.querySelector('.stext').textContent += text;
  term.scrollTop = term.scrollHeight;
}

// ── Add a message to the feed ─────────────────────────────────────────────────
function addMsg({ from, to, fromName, toName, message }) {
  // Remove placeholder
  feedList.querySelector('.feed-empty')?.remove();

  msgCount++;
  $('msgCount').textContent = `${msgCount} msg${msgCount !== 1 ? 's' : ''}`;

  const fromColor = agentMeta.get(from)?.color || '#8888ab';
  const toColor   = to === 'all' ? '#555570' : agentMeta.get(to)?.color || '#555570';
  const toDisplay = to === 'all' ? '📢 All' : (toName || to);

  const el = document.createElement('div');
  el.className = 'msg-item';
  el.innerHTML = `
    <div class="msg-meta">
      <span class="msg-from" style="color:${fromColor}">${esc(fromName || from)}</span>
      <span class="msg-arr">→</span>
      <span class="msg-to"  style="color:${toColor}">${esc(toDisplay)}</span>
      <span class="msg-time">${now()}</span>
    </div>
    <div class="msg-body">${esc(message)}</div>`;

  feedList.appendChild(el);
  feedList.scrollTop = feedList.scrollHeight;
}

// ── Socket events ─────────────────────────────────────────────────────────────

socket.on('agent:created', data => {
  const { id, role, title, emoji, color, task } = data;
  const c = color || (role === 'manager' ? '#ffd700' : WORKER_COLORS[workerIdx++ % WORKER_COLORS.length]);

  agentMeta.set(id, { color: c, role, title });

  // Remove empty state
  $('emptyState')?.remove();

  const card = createCard({ id, role, title, emoji, color: c, task });
  grid.appendChild(card);

  $('agentCount').textContent = `${agentMeta.size} Agent${agentMeta.size !== 1 ? 's' : ''}`;
});

socket.on('agent:status', ({ id, status }) => {
  setStatus(id, status);
});

socket.on('agent:stream', ({ id, text }) => {
  streamText(id, text);
});

socket.on('agent:message', data => {
  addMsg(data);
});

socket.on('agent:error', ({ id, error }) => {
  const term = $(`term-${id}`);
  if (!term) return;
  const line = document.createElement('div');
  line.className = 't-line';
  line.innerHTML = `<span style="color:#ef4444">⚠ ${esc(error)}</span>`;
  term.appendChild(line);
  term.scrollTop = term.scrollHeight;
});

socket.on('task:complete', ({ report }) => {
  // Re-enable input
  startBtn.disabled = false;
  startBtn.querySelector('.btn-label').textContent = 'Launch Agents';

  // Show report
  $('reportBody').textContent = report;
  $('reportOverlay').style.display = 'flex';
});

socket.on('task:error', ({ message }) => {
  startBtn.disabled = false;
  startBtn.querySelector('.btn-label').textContent = 'Launch Agents';
  alert(`Error: ${message}`);
});

// ── Report panel controls ──────────────────────────────────────────────────────
$('reportClose').addEventListener('click', () => {
  $('reportOverlay').style.display = 'none';
});
$('newTaskBtn').addEventListener('click', () => {
  $('reportOverlay').style.display = 'none';
  resetUI();
  taskIn.value = '';
  taskIn.focus();
});
// Close on backdrop click
$('reportOverlay').addEventListener('click', e => {
  if (e.target === $('reportOverlay')) $('reportOverlay').style.display = 'none';
});

// ── Connection indicator ───────────────────────────────────────────────────────
socket.on('connect',    () => { $('sysStatus').innerHTML = '<span class="sys-dot active"></span><span>System Online</span>'; });
socket.on('disconnect', () => {
  $('sysStatus').innerHTML = '<span class="sys-dot"></span><span>Reconnecting…</span>';
  startBtn.disabled = false;
  startBtn.querySelector('.btn-label').textContent = 'Launch Agents';
});
