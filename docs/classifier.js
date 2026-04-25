const SPORT_META = {
  soccer:     { it: 'Calcio',        emoji: '⚽' },
  tennis:     { it: 'Tennis',        emoji: '🎾' },
  basketball: { it: 'Pallacanestro', emoji: '🏀' },
  rugby:      { it: 'Rugby',         emoji: '🏉' },
  F1:         { it: 'Formula 1',     emoji: '🏎️' },
  baseball:   { it: 'Baseball',      emoji: '⚾' },
  golf:       { it: 'Golf',          emoji: '⛳' },
};

let modelData = null;

// ── Caricamento del modello ──────────────────────────────────────────────────

async function loadModel() {
  const resp = await fetch('model_data.json');
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  modelData = await resp.json();

  const btn  = document.getElementById('classify-btn');
  const text = document.getElementById('btn-text');
  btn.disabled     = false;
  text.className   = '';
  text.textContent = 'Classifica';
}

// ── Preprocessing ────────────────────────────────────────────────────────────

function tokenize(rawText) {
  return rawText
    .toLowerCase()
    .replace(/[^a-z\s]/g, '')
    .split(/\s+/)
    .filter(w => w.length >= 2);
}

// ── Softmax (stabilizzato) ───────────────────────────────────────────────────

function softmax(scores, temperature) {
  const T    = temperature || 1.0;
  const max  = Math.max(...scores);
  const exps = scores.map(s => Math.exp((s - max) / T));
  const sum  = exps.reduce((a, b) => a + b, 0);
  return exps.map(e => e / sum);
}

// ── TF-IDF sparso + decision function LinearSVC ──────────────────────────────

function classify(rawText) {
  const tokens = tokenize(rawText);
  if (tokens.length === 0) return null;

  const vocab     = modelData.vocabulary;
  const idf       = modelData.idf;
  const coef      = modelData.coef;
  const intercept = modelData.intercept;
  const classes   = modelData.classes;

  // TF: conta occorrenze solo per parole nel vocabolario
  const tf = {};
  for (const token of tokens) {
    const idx = vocab[token];
    if (idx !== undefined) tf[idx] = (tf[idx] || 0) + 1;
  }

  const entries = Object.entries(tf);
  if (entries.length === 0) return null;

  // TF-IDF con normalizzazione L2
  // sublinear_tf=true: tf = 1+log(count), riduce il peso dei termini ad alta frequenza
  // e rende la rappresentazione più robusta alla lunghezza dell'articolo
  const sublinear = modelData.sublinear_tf;
  let norm = 0;
  const tfidf = {};
  for (const [i, count] of entries) {
    const tf  = sublinear ? 1 + Math.log(count) : count;
    const val = tf * idf[+i];
    tfidf[i]  = val;
    norm     += val * val;
  }
  norm = Math.sqrt(norm);

  // Decision function su feature non-zero
  const scores = intercept.map((b, c) => {
    let s = b;
    for (const [i, val] of Object.entries(tfidf)) {
      s += coef[c][+i] * val / norm;
    }
    return s;
  });

  // Probabilità via softmax
  const probs = softmax(scores, modelData.temperature);

  // Lista ordinata per probabilità decrescente
  const ranked = classes
    .map((cls, i) => ({
      label: cls,
      pct:   Math.round(probs[i] * 1000) / 10,   // 1 decimale
    }))
    .sort((a, b) => b.pct - a.pct);

  const best = ranked[0];

  const bestScore = scores[classes.indexOf(best.label)];
  const threshold = modelData.thresholds
    ? modelData.thresholds[best.label]   // formato aggiornato (per-class)
    : modelData.threshold;               // fallback formato precedente (globale)

  return {
    label:     best.label,
    confident: bestScore >= threshold,
    pct:       best.pct,
    ranked,
  };
}

// ── Rendering risultato ──────────────────────────────────────────────────────

function buildBreakdown(ranked, topLabel) {
  return ranked.map(({ label, pct }) => {
    const meta    = SPORT_META[label] || { it: label, emoji: '🏆' };
    const isTop   = label === topLabel;
    return `
      <div class="prob-row${isTop ? ' prob-top' : ''}">
        <span class="prob-sport">${meta.emoji} ${meta.it}</span>
        <div class="prob-bar-wrap">
          <div class="prob-bar" style="width:${pct}%"></div>
        </div>
        <span class="prob-pct">${pct}%</span>
      </div>`;
  }).join('');
}

function showResult(prediction) {
  const resultDiv   = document.getElementById('result');
  const emojiEl     = document.getElementById('result-emoji');
  const labelEl     = document.getElementById('result-label');
  const confidEl    = document.getElementById('result-confidence');
  const msgEl       = document.getElementById('result-msg');
  const breakdownEl = document.getElementById('result-breakdown');

  if (confidEl)    confidEl.innerHTML    = '';
  if (breakdownEl) breakdownEl.innerHTML = '';

  // Testo non classificabile (troppo breve o fuori vocabolario)
  if (!prediction) {
    emojiEl.textContent = '❓';
    labelEl.textContent = 'Testo non riconoscibile';
    labelEl.className   = 'unknown';
    msgEl.textContent   = 'Il testo è troppo breve o non contiene parole riconoscibili.';
    resultDiv.classList.remove('hidden');
    return;
  }

  // ── Risultato principale: sempre il più probabile ────────────────────────
  const top     = prediction.ranked[0];
  const topMeta = SPORT_META[top.label] || { it: top.label, emoji: '🏆' };

  emojiEl.textContent = prediction.confident ? topMeta.emoji : '❓';
  labelEl.textContent = prediction.confident ? topMeta.it    : 'Altra categoria';
  labelEl.className   = prediction.confident ? 'known'       : 'unknown';
  msgEl.textContent   = prediction.confident
    ? ''
    : `Categoria più probabile: ${topMeta.emoji} ${topMeta.it}`;

  if (confidEl) {
    confidEl.innerHTML = `
      <div class="confidence-wrap">
        <div class="confidence-bar-track">
          <div class="confidence-bar-fill${prediction.confident ? '' : ' muted'}"
               id="conf-bar" style="width:0%"></div>
        </div>
        <span class="confidence-label">Confidenza: <strong>${top.pct}%</strong></span>
      </div>`;
    requestAnimationFrame(() => {
      const bar = document.getElementById('conf-bar');
      if (bar) bar.style.width = top.pct + '%';
    });
  }

  // ── Tutte le categorie, vincitrice evidenziata ───────────────────────────
  if (breakdownEl) {
    breakdownEl.innerHTML =
      '<div class="breakdown-title">Distribuzione categorie</div>' +
      buildBreakdown(prediction.ranked, top.label);
  }

  resultDiv.classList.remove('hidden');
  resultDiv.style.animation = 'none';
  void resultDiv.offsetWidth;
  resultDiv.style.animation = '';
}

// ── Init ─────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  loadModel().catch(() => {
    const text = document.getElementById('btn-text');
    text.className   = '';
    text.textContent = 'Errore nel caricamento del modello';
  });

  document.getElementById('classify-btn').addEventListener('click', () => {
    const raw = document.getElementById('article-input').value.trim();
    if (!raw) return;
    try {
      showResult(classify(raw));
    } catch (err) {
      console.error('Errore classificazione:', err);
      document.getElementById('result-emoji').textContent  = '⚠️';
      document.getElementById('result-label').textContent  = 'Errore';
      document.getElementById('result-label').className    = 'unknown';
      document.getElementById('result-msg').textContent    = 'Si è verificato un errore durante la classificazione. Controlla la console per i dettagli.';
      document.getElementById('result').classList.remove('hidden');
    }
  });

  document.getElementById('article-input').addEventListener('keydown', e => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      document.getElementById('classify-btn').click();
    }
  });
});
