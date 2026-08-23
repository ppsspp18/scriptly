'use strict';

const API_BASE = 'http://127.0.0.1:8000/api';
const SCENE_PAGE_SIZE = 10;

const els = {
  playFilter: document.getElementById('play-filter'),
  playList: document.getElementById('play-list'),
  scenePanel: document.getElementById('scene-panel'),
  scenePanelTitle: document.getElementById('scene-panel-title'),
  characterSearch: document.getElementById('character-search'),
  characterInput: document.getElementById('character-input'),
  characterBtn: document.getElementById('character-btn'),
  sceneList: document.getElementById('scene-list'),
  welcome: document.getElementById('welcome'),
  readerView: document.getElementById('reader-view'),
  playTitle: document.getElementById('play-title'),
  backBtn: document.getElementById('back-btn'),
  sidebarArrow: document.getElementById('sidebar-arrow'),
  sidebar: document.getElementById('sidebar'),
  prevScene: document.getElementById('prev-scene'),
  nextScene: document.getElementById('next-scene'),
  sceneLabel: document.getElementById('scene-label'),
  script: document.getElementById('script'),
  themeToggle: document.getElementById('theme-toggle'),
  status: document.getElementById('status'),
  askForm: document.getElementById('ask-form'),
  askInput: document.getElementById('ask-input'),
  askBtn: document.getElementById('ask-btn'),
  askResults: document.getElementById('ask-results'),
  insightsPanel: document.getElementById('insights-panel'),
  insightsContent: document.getElementById('insights-content'),
};

let plays = [];
let scenes = [];
let currentPlay = null;
let currentSceneIndex = -1;

/* ---------- utilities ---------- */

async function api(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status} for ${path}`);
  return res.json();
}

function showStatus(message, ms = 3000) {
  els.status.textContent = message;
  els.status.classList.remove('hidden');
  clearTimeout(showStatus._t);
  showStatus._t = setTimeout(() => els.status.classList.add('hidden'), ms);
}

function roman(n) {
  const map = ['0', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X',
    'XI', 'XII', 'XIII', 'XIV', 'XV', 'XVI', 'XVII', 'XVIII', 'XIX', 'XX'];
  return map[n] || String(n);
}

function esc(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/* ---------- plays ---------- */

async function loadPlays() {
  try {
    plays = await api('/plays/');
    renderPlayList('');
  } catch (err) {
    console.error(err);
    showStatus('Could not reach the API. Is the backend running on port 8000?', 8000);
  }
}

function renderPlayList(filter) {
  const q = filter.trim().toLowerCase();
  els.playList.innerHTML = '';
  plays
    .filter((p) => p.name.toLowerCase().includes(q))
    .forEach((p) => {
      const li = document.createElement('li');
      li.textContent = p.name.replace(/^\d+\s*/, '');
      li.dataset.id = p.id;
      if (currentPlay && currentPlay.id === p.id) li.classList.add('active');
      li.addEventListener('click', () => selectPlay(p));
      els.playList.appendChild(li);
    });
  if (!els.playList.children.length) {
    const li = document.createElement('li');
    li.textContent = 'No matching plays.';
    li.style.cursor = 'default';
    els.playList.appendChild(li);
  }
}

/* ---------- play / scenes ---------- */

async function selectPlay(play) {
  currentPlay = play;
  currentSceneIndex = -1;
  scenes = [];

  els.welcome.classList.add('hidden');
  els.readerView.classList.remove('hidden');
  els.scenePanel.classList.remove('hidden');
  els.characterSearch.classList.remove('hidden');
  els.scenePanelTitle.textContent = `${play.name} — Scenes`;
  els.playTitle.textContent = play.name;
  els.script.innerHTML = '';
  els.sceneLabel.textContent = 'Loading scenes…';
  markActivePlay();

  try {
    scenes = await api(`/plays/${play.id}/scenes/`);
    renderSceneList();
    if (scenes.length) loadScene(0);
  } catch (err) {
    console.error(err);
    els.sceneList.innerHTML = '<p>Failed to load scenes.</p>';
  }
}

function markActivePlay() {
  for (const li of els.playList.children) {
    li.classList.toggle('active', currentPlay && Number(li.dataset.id) === currentPlay.id);
  }
}

function renderSceneList() {
  els.sceneList.innerHTML = '';
  const byAct = new Map();
  scenes.forEach((s, i) => {
    if (!byAct.has(s.act)) byAct.set(s.act, []);
    byAct.get(s.act).push({ ...s, index: i });
  });

  for (const [act, actScenes] of byAct) {
    const group = document.createElement('div');
    group.className = 'act-group';
    const title = document.createElement('div');
    title.className = 'act-title';
    title.textContent = `Act ${roman(act)}`;
    const grid = document.createElement('div');
    grid.className = 'scene-grid';
    actScenes.forEach((s) => {
      const btn = document.createElement('button');
      btn.className = 'scene-btn';
      btn.textContent = `S${s.scene}`;
      btn.title = `Act ${roman(s.act)}, Scene ${s.scene}`;
      btn.addEventListener('click', () => {
        closeMobileSidebar();
        loadScene(s.index);
      });
      grid.appendChild(btn);
    });
    group.append(title, grid);
    els.sceneList.appendChild(group);
  }
}

/* ---------- script rendering ---------- */

async function loadScene(index) {
  currentSceneIndex = index;
  const scene = scenes[index];
  if (!scene) return;

  updateSceneNav();
  highlightSceneButtons();
  els.script.innerHTML = '<p class="stage-direction">Loading…</p>';

  try {
    const speeches = await api(`/scenes/${scene.id}/speeches/`);
    els.sceneLabel.textContent =
      `${currentPlay.name} — Act ${roman(scene.act)}, Scene ${scene.scene}`;
    renderSpeeches(speeches);
    loadInsights(scene.id);
  } catch (err) {
    console.error(err);
    els.script.innerHTML = '<p class="stage-direction">Failed to load this scene.</p>';
  }
}

function updateSceneNav() {
  els.prevScene.disabled = currentSceneIndex <= 0;
  els.nextScene.disabled = currentSceneIndex >= scenes.length - 1;
}

function highlightSceneButtons() {
  const buttons = els.sceneList.querySelectorAll('.scene-btn');
  buttons.forEach((b, i) => b.classList.toggle('active', i === currentSceneIndex));
}

function renderSpeeches(speeches) {
  els.script.innerHTML = '';
  let lastSpeaker = null;
  speeches.forEach((sp) => {
    const speechEl = document.createElement('div');
    speechEl.className = 'speech';

    const text = (sp.text || '').trim();
    const isStageDirection =
      sp.character_name === '' || /^\[.*\]$/.test(text) || /^\(.*\)$/.test(text);

    if (isStageDirection && !text) return;

    if (isStageDirection) {
      const dir = document.createElement('p');
      dir.className = 'stage-direction';
      dir.textContent = text;
      els.script.appendChild(dir);
      return;
    }

    if (sp.character_name === lastSpeaker) {
      speechEl.classList.add('continuous');
    } else {
      const speaker = document.createElement('span');
      speaker.className = 'speaker';
      speaker.textContent = sp.character_name;
      speechEl.appendChild(speaker);
    }
    lastSpeaker = sp.character_name;

    const p = document.createElement('p');
    p.className = 'text';
    p.textContent = text;
    speechEl.appendChild(p);
    els.script.appendChild(speechEl);
  });
  window.scrollTo({ top: 0 });
}

/* ---------- character lines view ---------- */

async function showCharacterLines() {
  const name = els.characterInput.value.trim();
  if (!name || !currentPlay) return;
  closeMobileSidebar();
  els.script.innerHTML = '<p class="stage-direction">Searching…</p>';

  try {
    const lines = await api(
      `/plays/${currentPlay.id}/characters/${encodeURIComponent(name)}/speeches/`
    );
    els.sceneLabel.textContent = `Lines by ${lines.length ? lines[0].character_name : name}`;
    els.prevScene.disabled = true;
    els.nextScene.disabled = true;
    highlightSceneButtons();

    if (!lines.length) {
      els.script.innerHTML =
        `<p class="stage-direction">No lines found for “${esc(name)}” in this play.</p>`;
      return;
    }

    els.script.innerHTML = `<p class="char-view-label">${lines.length} speeches by ${esc(lines[0].character_name)}</p>`;
    let lastActScene = null;
    lines.forEach((sp) => {
      const marker = `act ${sp.act}, scene ${sp.scene}`;
      if (marker !== lastActScene) {
        const head = document.createElement('p');
        head.className = 'char-view-label';
        head.style.marginTop = '1rem';
        head.textContent = `Act ${roman(sp.act)}, Scene ${sp.scene}`;
        els.script.appendChild(head);
        lastActScene = marker;
      }
      const p = document.createElement('p');
      p.className = 'text';
      p.textContent = (sp.text || '').trim();
      els.script.appendChild(p);
    });
    window.scrollTo({ top: 0 });
  } catch (err) {
    console.error(err);
    els.script.innerHTML = '<p class="stage-direction">Search failed.</p>';
  }
}

/* ---------- AI: Ask Scriptly (RAG + semantic cache) ---------- */

function sourceBadge(source, seconds) {
  const t = `${seconds}s`;
  if (source === 'semantic_cache') {
    return `<span class="badge badge-cache">⚡ Cached (${t})</span>`;
  }
  return `<span class="badge badge-pipeline">🤖 LangGraph Pipeline (${t})</span>`;
}

function renderMarkdown(text) {
  const raw = marked.parse(text || '', { breaks: true, gfm: true });
  return DOMPurify.sanitize(raw);
}

async function askScriptly(event) {
  event.preventDefault();
  const query = els.askInput.value.trim();
  if (!query) return;

  els.askBtn.disabled = true;
  const loading = document.createElement('div');
  loading.className = 'ask-item';
  loading.innerHTML = '<p class="stage-direction">Consulting the bard…</p>';
  els.askResults.prepend(loading);

  try {
    const res = await fetch(`${API_BASE}/ask/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `API error ${res.status}`);

    loading.remove();
    const item = document.createElement('div');
    item.className = 'ask-item';
    const citations = data.citations || [];
    item.innerHTML = `
      <div class="ask-meta">${sourceBadge(data.source, data.time_seconds)}</div>
      <div class="answer md">${renderMarkdown(data.answer)}</div>
      ${citations.length ? `
        <div class="citations">
          <span class="cite-label">Sources:</span>
          ${citations.map((c, i) => `
            <button class="citation" data-idx="${i}"
              title="Jump to ${esc(c.play_name)}, Act ${roman(c.act)}, Scene ${c.scene}">
              ${esc((c.play_name || '').replace(/^\d+\s*/, ''))} — Act ${roman(c.act)}, Sc ${c.scene}
            </button>`).join('')}
        </div>` : ''}
    `;
    item.querySelectorAll('.citation').forEach((btn) => {
      btn.addEventListener('click', () => jumpToCitation(citations[Number(btn.dataset.idx)]));
    });
    els.askResults.prepend(item);
    els.askInput.value = '';
  } catch (err) {
    console.error(err);
    loading.remove();
    els.askResults.prepend(
      Object.assign(document.createElement('div'), {
        className: 'ask-item',
        innerHTML: `<p class="stage-direction">${esc(err.message)}</p>`,
      })
    );
  } finally {
    els.askBtn.disabled = false;
  }
}

/* ---------- Interactive citation jumping (deep linking) ---------- */

async function jumpToCitation(citation) {
  if (!citation) return;
  const norm = (s) => (s || '').toLowerCase().replace(/^\d+\s*/, '').trim();
  const play = plays.find((p) => norm(p.name) === norm(citation.play_name));
  const target = play || currentPlay;
  if (!target) return;

  if (!currentPlay || currentPlay.id !== target.id) {
    await selectPlay(target);
  }

  const idx = scenes.findIndex(
    (s) => s.act === citation.act && s.scene === citation.scene
  );
  if (idx >= 0) loadScene(idx);
}

/* ---------- Entity & character insights panel ---------- */

const insightsCache = new Map();

async function loadInsights(sceneId) {
  if (!insightsCache.has(sceneId)) {
    try {
      insightsCache.set(sceneId, await api(`/scenes/${sceneId}/insights/`));
    } catch (err) {
      console.error(err);
      return;
    }
  }
  const data = insightsCache.get(sceneId);
  const hasAny = data.characters.length || data.locations.length || data.themes.length;
  els.insightsPanel.classList.toggle('hidden', !hasAny);
  if (!hasAny) return;

  const chipRow = (label, items) =>
    items.length
      ? `<div class="chip-group"><span class="chip-label">${label}</span>
          <div class="chips">${items
            .map((e) => `<span class="chip" title="Mentioned ${e.count}×">${esc(e.text)}</span>`)
            .join('')}</div></div>`
      : '';

  els.insightsContent.innerHTML = [
    chipRow('Characters', data.characters),
    chipRow('Locations', data.locations),
    chipRow('Themes & Entities', data.themes),
  ].join('');
}

/* ---------- events ---------- */

els.backBtn.addEventListener('click', () => {
  els.readerView.classList.add('hidden');
  els.welcome.classList.remove('hidden');
  els.scenePanel.classList.add('hidden');
  els.insightsPanel.classList.add('hidden');
  currentPlay = null;
  currentSceneIndex = -1;
  markActivePlay();
});

els.playFilter.addEventListener('input', (e) => renderPlayList(e.target.value));

els.prevScene.addEventListener('click', () => loadScene(currentSceneIndex - 1));
els.nextScene.addEventListener('click', () => loadScene(currentSceneIndex + 1));

els.characterBtn.addEventListener('click', showCharacterLines);
els.characterInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') showCharacterLines();
});

els.askForm.addEventListener('submit', askScriptly);

els.sidebarArrow.addEventListener('click', () => {
  const open = document.body.classList.toggle('sidebar-open');
  els.sidebarArrow.textContent = open ? '◀' : '▶';
  els.sidebarArrow.title = open ? 'Hide panel' : 'Show panel';
});

document.addEventListener('click', (e) => {
  if (
    window.innerWidth <= 800 &&
    document.body.classList.contains('sidebar-open') &&
    !els.sidebar.contains(e.target) &&
    !els.sidebarArrow.contains(e.target)
  ) {
    closeMobileSidebar();
  }
});

function closeMobileSidebar() {
  if (window.innerWidth <= 800) {
    document.body.classList.remove('sidebar-open');
    els.sidebarArrow.textContent = '▶';
  }
}

els.themeToggle.addEventListener('click', () => {
  const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = next;
  localStorage.setItem('scriptly-theme', next);
});

(function initTheme() {
  const saved = localStorage.getItem('scriptly-theme');
  if (saved) document.documentElement.dataset.theme = saved;
})();

loadPlays();
