/* ======================================================
   app.js — ATS Resume Analyzer — Frontend Logic
   ====================================================== */

'use strict';

// ── State ───────────────────────────────────────────────
const state = {
  selectedFile: null,
  currentAnalysis: null,
  historyData: [],
};

// ── DOM helpers ─────────────────────────────────────────
const $ = id => document.getElementById(id);
const qs = sel => document.querySelector(sel);
const qsa = sel => document.querySelectorAll(sel);

// ── Toast Notification ───────────────────────────────────
function showToast(message, type = 'info', duration = 4000) {
  const container = $('toastContainer');
  if (!container) return;

  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(24px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 350);
  }, duration);
}

// ── Loading Overlay ──────────────────────────────────────
function showLoading(msg = 'Analysing your resume…', sub = 'This may take a few seconds') {
  const overlay = $('loadingOverlay');
  if (!overlay) return;
  const textEl = overlay.querySelector('.loading-text');
  const subEl  = overlay.querySelector('.loading-sub');
  if (textEl) textEl.textContent = msg;
  if (subEl)  subEl.textContent = sub;
  overlay.classList.add('visible');
}
function hideLoading() {
  const overlay = $('loadingOverlay');
  if (overlay) overlay.classList.remove('visible');
}

// ── Navbar Mobile Toggle ─────────────────────────────────
function initNavbar() {
  const hamburger = $('hamburger');
  const navLinks  = $('navLinks');
  if (hamburger && navLinks) {
    hamburger.addEventListener('click', () => navLinks.classList.toggle('open'));
    document.addEventListener('click', e => {
      if (!hamburger.contains(e.target) && !navLinks.contains(e.target)) {
        navLinks.classList.remove('open');
      }
    });
  }

  // Highlight active link
  const path = window.location.pathname;
  qsa('.nav-links a').forEach(a => {
    if (a.getAttribute('href') === path ||
       (path === '/' && a.getAttribute('href') === '/')) {
      a.classList.add('active');
    }
  });
}

// ── Score Gauge ──────────────────────────────────────────
function animateGauge(score) {
  const fill   = $('gaugeFill');
  const valueEl = $('gaugeValue');
  const bandEl  = $('scoreBand');
  if (!fill || !valueEl) return;

  const circumference = 283;
  const offset = circumference - (score / 100) * circumference;

  // Colour based on score
  let colour, bandText, bandClass;
  if (score >= 80) {
    colour = '#22c55e'; bandText = 'Excellent Match'; bandClass = 'band-excellent';
  } else if (score >= 60) {
    colour = '#38bdf8'; bandText = 'Good Match'; bandClass = 'band-good';
  } else if (score >= 40) {
    colour = '#f59e0b'; bandText = 'Average Match'; bandClass = 'band-average';
  } else {
    colour = '#ef4444'; bandText = 'Poor Match'; bandClass = 'band-poor';
  }

  fill.style.stroke = colour;
  fill.style.strokeDashoffset = offset;
  if (bandEl) {
    bandEl.textContent = bandText;
    bandEl.className = `score-band ${bandClass}`;
  }

  // Animate counter
  let current = 0;
  const step = score / 60;
  const timer = setInterval(() => {
    current = Math.min(current + step, score);
    valueEl.textContent = Math.round(current);
    if (current >= score) clearInterval(timer);
  }, 16);
}

// ── Progress bars ────────────────────────────────────────
function animateProgress(id, pct) {
  const el = $(id);
  if (el) {
    setTimeout(() => { el.style.width = `${Math.min(pct, 100)}%`; }, 100);
  }
}

// ── Render breakdown cards ───────────────────────────────
function renderBreakdown(analysis) {
  const bd = analysis.score_breakdown || {};
  const components = [
    { id: 'compKeyword',    label: 'Keyword Match',  weight: '40%', value: bd.keyword_match || 0,  colour: '#22c55e', rawPct: analysis.keyword_match },
    { id: 'compSimilarity', label: 'Text Similarity',weight: '30%', value: bd.similarity    || 0,  colour: '#38bdf8', rawPct: analysis.similarity_score },
    { id: 'compExperience', label: 'Experience',     weight: '20%', value: bd.experience    || 0,  colour: '#a855f7', rawPct: (bd.experience || 0) / 0.20 },
    { id: 'compFormatting', label: 'Formatting',     weight: '10%', value: bd.formatting    || 0,  colour: '#f59e0b', rawPct: (bd.formatting || 0) / 0.10 },
  ];

  const container = $('breakdownGrid');
  if (!container) return;
  container.innerHTML = '';

  components.forEach(c => {
    const card = document.createElement('div');
    card.className = 'breakdown-card';
    card.innerHTML = `
      <div class="breakdown-label">${c.label}</div>
      <div class="breakdown-value">${c.value.toFixed(1)}</div>
      <div class="breakdown-weight">of 100 (weight ${c.weight})</div>
      <div class="progress-bar" style="margin-top:0.75rem">
        <div class="progress-fill" id="prog_${c.id}" style="background:${c.colour}"></div>
      </div>`;
    container.appendChild(card);
    // Animate bar
    const rawPct = Math.min(Math.max(c.rawPct || 0, 0), 100);
    setTimeout(() => {
      const bar = card.querySelector('.progress-fill');
      if (bar) bar.style.width = `${rawPct}%`;
    }, 200);
  });
}

// ── Render keyword tags ──────────────────────────────────
function renderTags(containerEl, keywords, type) {
  if (!containerEl) return;
  if (!keywords || keywords.length === 0) {
    containerEl.innerHTML = `<span class="text-muted" style="font-size:0.85rem">None detected.</span>`;
    return;
  }
  containerEl.innerHTML = keywords.map(kw =>
    `<span class="tag tag-${type}">
       ${type === 'matched' ? '✓' : '✗'} ${escHtml(kw)}
     </span>`
  ).join('');
}

// ── Render feedback list ─────────────────────────────────
function renderFeedbackList(containerEl, items, type) {
  if (!containerEl) return;
  if (!items || items.length === 0) {
    containerEl.innerHTML = '';
    return;
  }
  const icons = { suggestion: '💡', strength: '⭐', weak: '⚠️' };
  containerEl.innerHTML = `<ul class="feedback-list">${
    items.map((item, i) => `
      <li class="feedback-item ${type}" style="animation-delay:${i * 60}ms">
        <span class="feedback-icon">${icons[type]}</span>
        <span>${escHtml(item)}</span>
      </li>`).join('')
  }</ul>`;
}

// ── Render structure checks ──────────────────────────────
function renderStructureChecks(containerEl, checks) {
  if (!containerEl || !checks) return;
  containerEl.innerHTML = Object.entries(checks).map(([section, passed]) => `
    <div class="structure-item ${passed ? 'structure-pass' : 'structure-fail'}">
      <span>${passed ? '✅' : '❌'}</span>
      <span>${escHtml(section)}</span>
    </div>`
  ).join('');
}

// ── Render full analysis result ──────────────────────────
function renderAnalysis(data) {
  state.currentAnalysis = data;

  const resultsSection = $('resultsSection');
  if (resultsSection) resultsSection.classList.remove('hidden');

  // Gauge
  animateGauge(data.ats_score || 0);

  // Summary scores
  const setEl = (id, val) => { const el = $(id); if (el) el.textContent = val; };
  setEl('scoreKeyword',    (data.keyword_match || 0).toFixed(1) + '%');
  setEl('scoreSimilarity', (data.similarity_score || 0).toFixed(1) + '%');
  setEl('analysisId',      '#' + data.analysis_id);
  setEl('predictedCategory', data.predicted_category || '—');

  // Breakdown
  renderBreakdown(data);

  // Keywords
  renderTags($('matchedKeywords'), data.matched_keywords || [], 'matched');
  renderTags($('missingKeywords'), data.missing_keywords || [], 'missing');

  // Feedback
  renderFeedbackList($('strengthsList'),   data.strengths   || [], 'strength');
  renderFeedbackList($('suggestionsList'), data.suggestions || [], 'suggestion');
  renderFeedbackList($('weakAreasList'),   data.weak_areas  || [], 'weak');

  // Structure checks
  renderStructureChecks($('structureChecks'), data.structure_checks);

  // Disclaimer
  const discEl = $('disclaimerText');
  if (discEl && data.disclaimer) discEl.textContent = data.disclaimer;

  // Download button
  const dlBtn = $('downloadReportBtn');
  if (dlBtn && data.analysis_id) {
    dlBtn.href = `/api/report/${data.analysis_id}`;
    dlBtn.classList.remove('hidden');
  }

  // Scroll into view
  if (resultsSection) {
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

// ── Upload form submit ───────────────────────────────────
function initAnalyzeForm() {
  const form = $('analyzeForm');
  if (!form) return;

  // Drag-and-drop
  const dropZone = $('dropZone');
  const fileInput = $('resumeFile');
  if (dropZone) {
    ['dragenter', 'dragover'].forEach(ev => {
      dropZone.addEventListener(ev, e => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
      });
    });
    ['dragleave', 'drop'].forEach(ev => {
      dropZone.addEventListener(ev, e => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
      });
    });
    dropZone.addEventListener('drop', e => {
      const files = e.dataTransfer.files;
      if (files.length > 0) handleFileSelect(files[0]);
    });
  }

  if (fileInput) {
    fileInput.addEventListener('change', () => {
      if (fileInput.files.length > 0) handleFileSelect(fileInput.files[0]);
    });
  }

  // JD char count
  const jdTextarea = $('jobDescription');
  const charCount  = $('charCount');
  if (jdTextarea && charCount) {
    jdTextarea.addEventListener('input', () => {
      charCount.textContent = jdTextarea.value.length + ' characters';
    });
  }

  // Remove file button
  const removeBtn = $('removeFileBtn');
  if (removeBtn) {
    removeBtn.addEventListener('click', () => {
      state.selectedFile = null;
      if (fileInput) fileInput.value = '';
      const selected = $('fileSelected');
      if (selected) selected.classList.remove('visible');
    });
  }

  // Submit
  form.addEventListener('submit', async e => {
    e.preventDefault();

    if (!state.selectedFile) {
      showToast('Please select a resume file (PDF or DOCX).', 'error');
      return;
    }
    const jd = jdTextarea ? jdTextarea.value.trim() : '';
    if (!jd || jd.length < 30) {
      showToast('Please enter a meaningful job description (at least 30 characters).', 'error');
      return;
    }

    const fd = new FormData();
    fd.append('resume', state.selectedFile);
    fd.append('job_description', jd);

    showLoading('Parsing your resume…', 'Extracting text and running NLP analysis');
    const analyzeBtn = $('analyzeBtn');
    if (analyzeBtn) analyzeBtn.disabled = true;

    try {
      const res = await fetch('/api/analyze', { method: 'POST', body: fd });
      const data = await res.json();

      if (!data.success) {
        showToast(data.error || 'Analysis failed. Please try again.', 'error');
        return;
      }

      showToast('Analysis complete! 🎉', 'success');
      renderAnalysis({ ...data, analysis_id: data.analysis_id });
    } catch (err) {
      showToast('Network error. Is the server running?', 'error');
      console.error(err);
    } finally {
      hideLoading();
      if (analyzeBtn) analyzeBtn.disabled = false;
    }
  });
}

function handleFileSelect(file) {
  const allowed = ['application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
  const ext = file.name.split('.').pop().toLowerCase();

  if (!['pdf', 'docx'].includes(ext)) {
    showToast('Only PDF and DOCX files are supported.', 'error');
    return;
  }
  const maxBytes = 5 * 1024 * 1024;
  if (file.size > maxBytes) {
    showToast(`File too large. Max size is 5 MB.`, 'error');
    return;
  }

  state.selectedFile = file;
  const selected = $('fileSelected');
  if (selected) {
    selected.classList.add('visible');
    const nameEl = selected.querySelector('.file-name');
    const sizeEl = selected.querySelector('.file-size');
    if (nameEl) nameEl.textContent = file.name;
    if (sizeEl) sizeEl.textContent = formatBytes(file.size);
  }
  showToast(`File selected: ${file.name}`, 'success', 2500);
}

// ── History page ─────────────────────────────────────────
async function initHistoryPage() {
  const tableBody = $('historyTableBody');
  const emptyState = $('historyEmpty');
  if (!tableBody) return;

  try {
    const res  = await fetch('/api/history?per_page=50');
    const data = await res.json();

    if (!data.success || !data.analyses || data.analyses.length === 0) {
      if (emptyState) emptyState.classList.remove('hidden');
      return;
    }

    state.historyData = data.analyses;
    if (emptyState) emptyState.classList.add('hidden');

    tableBody.innerHTML = data.analyses.map(a => {
      const score = a.ats_score || 0;
      const pillCls = score >= 70 ? 'score-pill-high' : score >= 50 ? 'score-pill-medium' : 'score-pill-low';
      const date = a.created_at ? new Date(a.created_at).toLocaleString() : '—';
      return `
        <tr>
          <td>#${a.id}</td>
          <td>${escHtml(a.original_filename || '—')}</td>
          <td><span class="score-pill ${pillCls}">${score.toFixed(1)}</span></td>
          <td>${(a.keyword_match_score || 0).toFixed(1)}%</td>
          <td>${(a.similarity_score || 0).toFixed(1)}%</td>
          <td>${escHtml(a.predicted_category || '—')}</td>
          <td>${date}</td>
          <td>
            <div class="flex gap-1">
              <a href="/result/${a.id}" class="btn btn-sm btn-secondary">View</a>
              <a href="/api/report/${a.id}" class="btn btn-sm btn-secondary" download>PDF</a>
            </div>
          </td>
        </tr>`;
    }).join('');

    // Populate compare dropdowns
    populateCompareDropdowns(data.analyses);
  } catch (err) {
    showToast('Failed to load history.', 'error');
    console.error(err);
  }
}

function populateCompareDropdowns(analyses) {
  const prevSel = $('comparePrev');
  const newSel  = $('compareNew');
  if (!prevSel || !newSel) return;

  const options = analyses.map(a =>
    `<option value="${a.id}">#${a.id} — ${escHtml(a.original_filename || '?')} (${(a.ats_score||0).toFixed(1)})</option>`
  ).join('');
  prevSel.innerHTML = `<option value="">— select —</option>` + options;
  newSel.innerHTML  = `<option value="">— select —</option>` + options;
}

async function runCompare() {
  const prevId = $('comparePrev')?.value;
  const newId  = $('compareNew')?.value;
  if (!prevId || !newId) { showToast('Select both analyses to compare.', 'error'); return; }
  if (prevId === newId)  { showToast('Select two different analyses.', 'error'); return; }

  showLoading('Comparing analyses…', '');
  try {
    const res  = await fetch('/api/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ previous_id: parseInt(prevId), new_id: parseInt(newId) }),
    });
    const data = await res.json();
    if (!data.success) { showToast(data.error || 'Comparison failed.', 'error'); return; }
    renderComparison(data.comparison);
  } catch (err) {
    showToast('Network error.', 'error');
  } finally {
    hideLoading();
  }
}

function renderComparison(comp) {
  const section = $('comparisonResult');
  if (!section) return;
  section.classList.remove('hidden');

  const diff = comp.score_difference || 0;
  const deltaClass = diff > 0 ? 'delta-positive' : diff < 0 ? 'delta-negative' : 'delta-neutral';
  const deltaSign  = diff > 0 ? '+' : '';

  const prevBd = comp.previous_breakdown || {};
  const newBd  = comp.new_breakdown || {};

  section.innerHTML = `
    <div class="card">
      <div class="card-title"><div class="card-icon">📊</div> Before vs After Comparison</div>
      <div class="comparison-scores">
        <div class="score-bubble">
          <div class="score-number">${(comp.previous_score || 0).toFixed(1)}</div>
          <div class="score-label">Previous</div>
        </div>
        <div class="score-arrow">→</div>
        <div class="score-bubble">
          <div class="score-number">${(comp.new_score || 0).toFixed(1)}</div>
          <div class="score-label">Updated</div>
        </div>
        <span class="score-delta ${deltaClass}">${deltaSign}${diff.toFixed(1)} pts</span>
      </div>

      <div class="section-label">Breakdown Comparison</div>
      <div class="breakdown-grid" style="margin-bottom:1rem">
        ${['keyword_match','similarity','experience','formatting'].map(key => `
          <div class="breakdown-card">
            <div class="breakdown-label">${key.replace('_',' ')}</div>
            <div style="display:flex;gap:.4rem;align-items:baseline;font-size:.9rem">
              <span style="color:#94a3b8">${(prevBd[key]||0).toFixed(1)}</span>
              <span style="color:#94a3b8">→</span>
              <span style="font-weight:700">${(newBd[key]||0).toFixed(1)}</span>
            </div>
          </div>`).join('')}
      </div>

      ${comp.newly_matched_keywords?.length ? `
        <div class="section-label">Newly Matched Keywords</div>
        <div class="tag-container mb-1">${comp.newly_matched_keywords.map(k=>`<span class="tag tag-matched">✓ ${escHtml(k)}</span>`).join('')}</div>
      ` : ''}

      ${comp.still_missing_keywords?.length ? `
        <div class="section-label mt-2">Still Missing</div>
        <div class="tag-container mb-1">${comp.still_missing_keywords.map(k=>`<span class="tag tag-missing">✗ ${escHtml(k)}</span>`).join('')}</div>
      ` : ''}

      ${comp.new_suggestions?.length ? `
        <div class="section-label mt-2">Updated Suggestions</div>
        <ul class="feedback-list">${comp.new_suggestions.slice(0,5).map(s=>`
          <li class="feedback-item suggestion"><span class="feedback-icon">💡</span><span>${escHtml(s)}</span></li>`).join('')}</ul>
      ` : ''}
    </div>`;
  section.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ── Result page (single analysis) ───────────────────────
async function initResultPage() {
  const analysisId = window.location.pathname.split('/').pop();
  if (!analysisId || isNaN(analysisId)) return;

  showLoading('Loading analysis…', '');
  try {
    const res  = await fetch(`/api/analysis/${analysisId}`);
    const data = await res.json();
    if (!data.success) { showToast('Analysis not found.', 'error'); hideLoading(); return; }
    const a = data.analysis;
    renderAnalysis({ ...a, analysis_id: a.id });
  } catch (err) {
    showToast('Failed to load analysis.', 'error');
  } finally {
    hideLoading();
  }
}

// ── Tabs ─────────────────────────────────────────────────
function initTabs() {
  qsa('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.tab;
      const container = btn.closest('[data-tabs]') || document;
      container.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      container.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      const panel = container.querySelector(`#${target}`);
      if (panel) panel.classList.add('active');
    });
  });
}

// ── Utilities ────────────────────────────────────────────
function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

// ── Entry point ──────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initNavbar();
  initTabs();

  const path = window.location.pathname;

  if (path === '/' || path === '/index') {
    initAnalyzeForm();
  } else if (path.startsWith('/history')) {
    initHistoryPage();
    const compareBtn = $('runCompareBtn');
    if (compareBtn) compareBtn.addEventListener('click', runCompare);
  } else if (path.startsWith('/result/')) {
    initResultPage();
  }
});
