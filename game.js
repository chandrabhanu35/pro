'use strict';

// ─── Constants ───────────────────────────────────────────────────────────────

const COLORS   = ['red', 'blue', 'green', 'yellow'];
const SPECIALS = ['skip', 'reverse', 'draw2'];

const BOT_NAMES = [
    'AlexBot','ZaraAI','MaxBot','LunaAI','RioBot','NovaAI',
    'KaiBot','StarAI','BlazeBot','NeonAI','VexBot','OracleAI',
    'CypherBot','EchoAI','FluxBot','VortexAI','ZeroBot','ApexAI',
    'PhantomBot','CobraAI','ThunderBot','ShadowAI'
];

const BOT_CHAT = {
    play:    ['Let\'s go! 🔥','Watch this 😏','Easy 😎','Ha!','Your move!','Smooth play!','Too easy 😂'],
    draw:    ['Ugh 😩','Come on!','Not what I need...','Draw? Really?','Fine 😒'],
    skip:    ['Skipped! 😂','Sit down! 🤐','Next! 💨','Bye bye turn! 👋'],
    reverse: ['Direction flipped! 😈','Back it up! 🔄','Surprise! ↺'],
    draw2:   ['+2! Sorry 😂','Draw 2! 📤','Oops, +2 your way! 😈','Take those! 🎴'],
    wild:    ['Wild! Color change 🌈','My choice now 😏','Shake it up! ⭐','Wild card! 😈'],
    wild4:   ['+4! Destroyed 😂','Wild Draw 4! 💀','That\'s gotta hurt 😈','+4 incoming! 🚀'],
    uno:     ['UNO!!! 🎉','One card! Can you stop me? 😏','UNO baby! 🔥','Almost there! UNO!'],
    win:     ['I WIN! 🏆','GG! Too easy 😎','Victory! Better luck next time 😂','Unbeatable! 🎉'],
    react:   ['Nice move!','Interesting... 👀','You got lucky 😒','Good one!','I see you 👀','Hmm...','Wow!'],
    taunt:   ['You can\'t beat me 😏','Is that all? 😂','Tick tock! ⏰','Nervous? 😈'],
};

// ─── State ───────────────────────────────────────────────────────────────────

let G = {};          // game state
let currentMode = '1v1';
let botTimer    = null;
let gameStartTime = 0;

// ─── Deck ────────────────────────────────────────────────────────────────────

function buildDeck() {
    const deck = [];
    COLORS.forEach(c => {
        deck.push(card(c, '0', 'number'));
        for (let n = 1; n <= 9; n++) {
            deck.push(card(c, String(n), 'number'));
            deck.push(card(c, String(n), 'number'));
        }
        SPECIALS.forEach(s => {
            deck.push(card(c, s, 'action'));
            deck.push(card(c, s, 'action'));
        });
    });
    for (let i = 0; i < 4; i++) {
        deck.push(card('wild', 'wild',  'wild'));
        deck.push(card('wild', 'wild4', 'wild4'));
    }
    return deck;
}

function card(color, value, type) { return { color, value, type }; }

function shuffle(arr) {
    const a = [...arr];
    for (let i = a.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
}

function pickBotName(used = []) {
    const avail = BOT_NAMES.filter(n => !used.includes(n));
    return avail[Math.floor(Math.random() * avail.length)];
}

// ─── Game Init ────────────────────────────────────────────────────────────────

function startGame(mode) {
    currentMode = mode;
    clearBotTimer();

    const used = [];
    const players = [];

    players.push({ id: 0, name: 'You', isBot: false, hand: [], team: 0 });

    if (mode === '1v1') {
        const n = pickBotName(used); used.push(n);
        players.push({ id: 1, name: n, isBot: true, hand: [], team: 1 });
    } else {
        // 2v2: You(T0) + Bot(T0) vs Bot(T1) + Bot(T1)
        const n1 = pickBotName(used); used.push(n1);
        const n2 = pickBotName(used); used.push(n2);
        const n3 = pickBotName(used); used.push(n3);
        players.push({ id: 1, name: n1, isBot: true, hand: [], team: 0 });
        players.push({ id: 2, name: n2, isBot: true, hand: [], team: 1 });
        players.push({ id: 3, name: n3, isBot: true, hand: [], team: 1 });
    }

    let deck = shuffle(buildDeck());
    players.forEach(p => { p.hand = deck.splice(0, 7); });

    // First card must not be wild
    let startCard;
    do {
        startCard = deck.shift();
        if (startCard.type === 'wild' || startCard.type === 'wild4') {
            deck.push(startCard);
            startCard = null;
        }
    } while (!startCard);

    G = {
        deck,
        discard:        [startCard],
        players,
        current:        0,
        direction:      1,
        currentColor:   startCard.color,
        waitColor:      false,
        pendingDraw:    0,
        canDraw:        true,
        drewThisTurn:   false,
        gameOver:       false,
        unoCalled:      false,
        cardsPlayed:    0,
    };

    gameStartTime = Date.now();

    // Clear chat
    document.getElementById('chat-messages').innerHTML = '';

    showScreen('game');
    document.getElementById('mode-badge').textContent =
        mode === '1v1' ? '⚔️ 1 vs 1' : '🤝 2 vs 2';

    // Handle start card effect
    const top = topCard();
    sysMsg(`Game on! First card: ${cardLabel(top)}`);
    setTimeout(() => {
        const bot = players.find(p => p.isBot);
        if (bot) botSay(bot.name, rand(BOT_CHAT.react));
    }, 800);

    if (top.value === 'skip') {
        sysMsg('First Skip — your turn is skipped!');
        advance(); advance();
    } else if (top.value === 'reverse') {
        G.direction = -1;
        sysMsg('First Reverse — direction changed!');
        advance();
    } else if (top.value === 'draw2') {
        sysMsg('First Draw 2 — you draw 2 cards!');
        drawCards(0, 2);
        advance(); advance();
    }

    render();
    maybeScheduleBot();
}

// ─── Core Logic ──────────────────────────────────────────────────────────────

function topCard()        { return G.discard[G.discard.length - 1]; }
function totalPlayers()   { return G.players.length; }

function canPlay(c) {
    if (G.waitColor) return false;
    if (c.type === 'wild' || c.type === 'wild4') return true;
    return c.color === G.currentColor || c.value === topCard().value;
}

function advance() {
    G.current = (G.current + G.direction + totalPlayers()) % totalPlayers();
    G.canDraw = true;
    G.drewThisTurn = false;
}

function drawCards(idx, n) {
    for (let i = 0; i < n; i++) {
        if (G.deck.length === 0) reshuffleDeck();
        if (G.deck.length > 0) G.players[idx].hand.push(G.deck.shift());
    }
}

function reshuffleDeck() {
    if (G.discard.length <= 1) return;
    const top = G.discard.pop();
    G.deck    = shuffle(G.discard);
    G.discard = [top];
    sysMsg('Deck reshuffled!');
}

// ─── Play Card ───────────────────────────────────────────────────────────────

function playCard(playerIdx, cardIdx) {
    if (G.gameOver || G.waitColor) return;
    if (playerIdx !== G.current) return;

    const player = G.players[playerIdx];
    const c      = player.hand[cardIdx];
    if (!canPlay(c)) return;

    player.hand.splice(cardIdx, 1);
    G.discard.push(c);
    G.unoCalled   = false;
    G.cardsPlayed++;

    // UNO alert
    if (player.hand.length === 1) {
        if (player.isBot) {
            setTimeout(() => {
                botSay(player.name, rand(BOT_CHAT.uno));
                G.unoCalled = true;
            }, 350);
        } else {
            document.getElementById('uno-btn').classList.remove('hidden');
        }
    }

    // Penalty: forgot to call UNO (if player has 1 card left uncalled and it's not their turn anymore)
    // Simplified: just auto-penalise human if they had 1 card and didn't press UNO
    applyEffect(c, playerIdx);

    if (player.hand.length === 0) { winGame(playerIdx); return; }

    render();
    maybeScheduleBot();
}

function applyEffect(c, fromIdx) {
    if (c.type === 'wild' || c.type === 'wild4') {
        G.waitColor = true;
        if (c.type === 'wild4') G.pendingDraw = 4;

        if (G.players[fromIdx].isBot) {
            const best = botBestColor(G.players[fromIdx].hand);
            setTimeout(() => {
                botSay(G.players[fromIdx].name, rand(c.type === 'wild4' ? BOT_CHAT.wild4 : BOT_CHAT.wild));
                pickColor(best);
            }, 700);
        } else {
            document.getElementById('color-picker').classList.remove('hidden');
        }
        return;
    }

    G.currentColor = c.color;

    switch (c.value) {
        case 'skip':
            advance(); // skip next
            sysMsg(`${G.players[G.current].name} is skipped!`);
            advance();
            break;
        case 'reverse':
            G.direction *= -1;
            sysMsg('Direction reversed!');
            advance();
            if (totalPlayers() === 2) { advance(); } // In 2-player, reverse acts like skip
            break;
        case 'draw2':
            advance();
            drawCards(G.current, 2);
            sysMsg(`${G.players[G.current].name} draws 2!`);
            advance();
            break;
        default:
            advance();
    }
}

// ─── Player Actions ──────────────────────────────────────────────────────────

function drawCard() {
    if (G.gameOver || G.current !== 0 || !G.canDraw || G.waitColor) return;

    drawCards(0, 1);
    G.canDraw       = false;
    G.drewThisTurn  = true;

    const drawn = G.players[0].hand[G.players[0].hand.length - 1];
    if (canPlayDrawn(drawn)) {
        setStatus('Drew a playable card — play it or pass!', true);
        document.getElementById('pass-btn').classList.remove('hidden');
    } else {
        setStatus('No match — turn passed.');
        document.getElementById('pass-btn').classList.add('hidden');
        setTimeout(() => { advance(); render(); maybeScheduleBot(); }, 700);
    }

    document.getElementById('uno-btn').classList.add('hidden');
    render();
}

function canPlayDrawn(c) {
    if (c.type === 'wild' || c.type === 'wild4') return true;
    return c.color === G.currentColor || c.value === topCard().value;
}

function passTurn() {
    document.getElementById('pass-btn').classList.add('hidden');
    advance();
    render();
    maybeScheduleBot();
}

function pickColor(color) {
    G.currentColor = color;
    G.waitColor    = false;
    document.getElementById('color-picker').classList.add('hidden');
    sysMsg(`Color → ${color.toUpperCase()}`);
    updateColorRing();

    if (G.pendingDraw > 0) {
        advance();
        drawCards(G.current, G.pendingDraw);
        sysMsg(`${G.players[G.current].name} draws ${G.pendingDraw}!`);
        G.pendingDraw = 0;
        advance();
    } else {
        advance();
    }

    render();
    maybeScheduleBot();
}

function callUno() {
    G.unoCalled = true;
    document.getElementById('uno-btn').classList.add('hidden');
    sysMsg('You called UNO! 🎉');
    addChat('You', 'UNO!!! 🎉', 'player');
}

// ─── Bot AI ──────────────────────────────────────────────────────────────────

function maybeScheduleBot() {
    if (G.gameOver || G.waitColor) return;
    const p = G.players[G.current];
    if (p && p.isBot) scheduleBotTurn();
}

function scheduleBotTurn() {
    clearBotTimer();
    const delay = 1000 + Math.random() * 900;
    botTimer = setTimeout(botTurn, delay);
}

function clearBotTimer() {
    if (botTimer) { clearTimeout(botTimer); botTimer = null; }
}

function botTurn() {
    if (G.gameOver || G.waitColor) return;
    const p = G.players[G.current];
    if (!p || !p.isBot) return;

    const playable = p.hand
        .map((c, i) => ({ c, i }))
        .filter(({ c }) => canPlay(c));

    if (playable.length > 0) {
        const chosen = botChoose(playable, p);

        // Chat
        const chatKey = chosen.c.value === 'wild4' ? 'wild4'
                      : chosen.c.value === 'wild'   ? 'wild'
                      : chosen.c.value === 'draw2'  ? 'draw2'
                      : chosen.c.value === 'skip'   ? 'skip'
                      : chosen.c.value === 'reverse'? 'reverse'
                      : 'play';
        if (Math.random() < 0.38) botSay(p.name, rand(BOT_CHAT[chatKey]));

        playCard(G.current, chosen.i);
    } else {
        if (Math.random() < 0.3) botSay(p.name, rand(BOT_CHAT.draw));
        drawCards(G.current, 1);
        sysMsg(`${p.name} draws a card`);
        advance();
        render();
        maybeScheduleBot();
    }
}

function botChoose(playable, player) {
    // Priority order
    const priorities = ['wild4', 'draw2', 'skip', 'reverse', 'wild'];
    for (const v of priorities) {
        const found = playable.find(({ c }) => c.value === v);
        if (found) return found;
    }
    // Prefer matching color with highest number
    const colorMatch = playable.filter(({ c }) => c.color === G.currentColor);
    if (colorMatch.length > 0) {
        return colorMatch.sort((a, b) => parseInt(b.c.value || 0) - parseInt(a.c.value || 0))[0];
    }
    return playable[0];
}

function botBestColor(hand) {
    const count = { red: 0, blue: 0, green: 0, yellow: 0 };
    hand.forEach(c => { if (count[c.color] !== undefined) count[c.color]++; });
    return Object.entries(count).sort((a, b) => b[1] - a[1])[0][0];
}

// ─── Win ─────────────────────────────────────────────────────────────────────

function winGame(winnerIdx) {
    G.gameOver = true;
    clearBotTimer();
    const winner = G.players[winnerIdx];

    if (winner.isBot) {
        setTimeout(() => botSay(winner.name, rand(BOT_CHAT.win)), 300);
    }

    const elapsed   = Math.round((Date.now() - gameStartTime) / 1000);
    const mins      = Math.floor(elapsed / 60);
    const secs      = elapsed % 60;
    const duration  = mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;

    const isPlayer   = winnerIdx === 0;
    const isTeammate = currentMode === '2v2' && winner.team === 0 && winnerIdx !== 0;
    const playerWins = isPlayer || isTeammate;

    setTimeout(() => {
        document.getElementById('win-emoji').textContent  = playerWins ? '🏆' : '😢';
        document.getElementById('win-title').textContent  = playerWins ? (isPlayer ? 'You Win!' : 'Your Team Wins!') : `${winner.name} Wins!`;
        document.getElementById('win-msg').textContent    = playerWins
            ? 'Amazing play! You crushed it! 🔥'
            : `${winner.name} dominated this round! 😈`;
        document.getElementById('win-stats').innerHTML = `
            🕐 Duration: <strong>${duration}</strong><br>
            🃏 Cards played: <strong>${G.cardsPlayed}</strong><br>
            👥 Players: <strong>${G.players.map(p => p.name).join(', ')}</strong>
        `;
        showScreen('win');
    }, 900);
}

// ─── Render ──────────────────────────────────────────────────────────────────

function render() {
    if (G.gameOver) return;
    renderTopCard();
    renderPlayerHand();
    renderOpponents();
    renderTurnBar();
    updateColorRing();
    updateDeckCount();
    updateHandCount();
}

function renderTopCard() {
    const tc  = topCard();
    const el  = document.getElementById('top-card');
    el.className  = `card ${G.currentColor || tc.color} card-played`;
    el.innerHTML  = cardHTML(tc);
    setTimeout(() => el.classList.remove('card-played'), 280);
}

function cardHTML(c) {
    const lbl = cardLabel(c);
    return `<span class="corner tl">${lbl}</span>
            <span class="card-center">${lbl}</span>
            <span class="corner br">${lbl}</span>`;
}

function cardLabel(c) {
    const map = { skip:'🚫', reverse:'↺', draw2:'+2', wild:'★', wild4:'+4' };
    return map[c.value] ?? c.value;
}

function renderPlayerHand() {
    const p     = G.players[0];
    const el    = document.getElementById('player-hand');
    const myTurn = G.current === 0;
    el.innerHTML = '';

    p.hand.forEach((c, idx) => {
        const div = document.createElement('div');
        const justDrewThis = G.drewThisTurn && idx === p.hand.length - 1;
        const playable = myTurn && canPlay(c) && (G.canDraw || justDrewThis);

        div.className = `card ${c.color} hand-card ${playable ? 'playable' : 'not-playable'}`;
        div.innerHTML = cardHTML(c);

        if (playable) {
            div.onclick = () => {
                G.canDraw       = true;
                G.drewThisTurn  = false;
                document.getElementById('pass-btn').classList.add('hidden');
                playCard(0, idx);
            };
        }
        el.appendChild(div);
    });
}

function renderOpponents() {
    const row = document.getElementById('opponents-row');
    row.innerHTML = '';

    G.players.slice(1).forEach(p => {
        const isActive = G.current === p.id;
        const div = document.createElement('div');
        div.className = `opponent-block${isActive ? ' active-player' : ''}`;

        const fanCount = Math.min(p.hand.length, 12);
        const fanHTML  = Array(fanCount).fill('<div class="card-back-mini"></div>').join('');
        const teamBadge = currentMode === '2v2'
            ? `<span class="opp-team-badge">${p.team === 0 ? '🟢 Ally' : '🔴 Enemy'}</span>` : '';

        div.innerHTML = `
            <div class="opp-name">
                ${isActive ? '<span class="active-dot"></span>' : ''}
                ${p.name} ${teamBadge}
            </div>
            <div class="opp-cards-fan">${fanHTML}</div>
            <div class="opp-count ${p.hand.length === 1 ? 'uno-alert' : ''}">${p.hand.length} card${p.hand.length !== 1 ? 's' : ''}</div>
        `;
        row.appendChild(div);
    });
}

function renderTurnBar() {
    const p  = G.players[G.current];
    const el = document.getElementById('turn-indicator');
    if (!p) return;
    if (p.isBot) {
        el.textContent = `${p.name} is thinking...`;
        el.className   = 'turn-indicator bot-turn';
    } else {
        el.textContent = 'Your Turn! ▶';
        el.className   = 'turn-indicator';
    }
}

function updateColorRing() {
    const el = document.getElementById('current-color-ring');
    el.className = `color-ring ${G.currentColor || ''}`;
}

function updateDeckCount() {
    document.getElementById('deck-count').textContent = `${G.deck.length} left`;
}

function updateHandCount() {
    const n = G.players[0].hand.length;
    document.getElementById('player-hand-count').textContent = `${n} card${n !== 1 ? 's' : ''}`;
}

function setStatus(msg, isAlert = false) {
    const el = document.getElementById('game-status');
    el.textContent = msg;
    el.className   = `game-status${isAlert ? ' alert' : ''}`;
}

// ─── Chat ────────────────────────────────────────────────────────────────────

function addChat(from, text, type) {
    const box = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `chat-msg ${type}`;
    div.innerHTML = `<span class="from">${from}</span>${text}`;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
}

function sysMsg(text) { addChat('🎮 Game', text, 'system'); }

function botSay(name, text) { addChat(name, text, 'bot'); }

function rand(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

function sendChat() {
    const input = document.getElementById('chat-input');
    const txt   = input.value.trim();
    if (!txt) return;
    addChat('You', txt, 'player');
    input.value = '';

    // Bot reacts sometimes
    if (!G.gameOver && Math.random() < 0.55) {
        const bots = G.players.filter(p => p.isBot);
        if (bots.length) {
            const bot = rand(bots);
            const reply = Math.random() < 0.3 ? rand(BOT_CHAT.taunt) : rand(BOT_CHAT.react);
            setTimeout(() => botSay(bot.name, reply), 600 + Math.random() * 600);
        }
    }
}

function chatKey(e) { if (e.key === 'Enter') sendChat(); }

function quickReact(emoji) {
    addChat('You', emoji, 'player');
    if (!G.gameOver && Math.random() < 0.5) {
        const bots = G.players.filter(p => p.isBot);
        if (bots.length) {
            const bot  = rand(bots);
            const emojis = ['😂','😤','🔥','👀','😏','💀','🤡'];
            setTimeout(() => botSay(bot.name, rand(emojis)), 500 + Math.random() * 400);
        }
    }
}

// ─── Screen Management ───────────────────────────────────────────────────────

function showScreen(name) {
    document.querySelectorAll('.screen').forEach(s => {
        s.classList.remove('active');
        s.style.display = 'none';
    });
    const s = document.getElementById(`${name}-screen`);
    s.style.display = 'flex';
    requestAnimationFrame(() => s.classList.add('active'));
}

function showMenu() {
    clearBotTimer();
    if (G && !G.gameOver) G.gameOver = true;
    showScreen('menu');
}

function confirmMenu() {
    if (G && !G.gameOver) {
        if (confirm('Leave current game?')) showMenu();
    } else {
        showMenu();
    }
}
