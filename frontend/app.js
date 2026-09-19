// Thunder Draft Scout - frontend logic. No build step: vanilla JS + Chart.js via CDN.
const API_BASE = "/api";

const state = { prospects: [], selectedId: null, radarChart: null };

const els = {
  list: document.getElementById("prospectList"),
  search: document.getElementById("prospectSearch"),
  emptyState: document.getElementById("emptyState"),
  report: document.getElementById("report"),
  dataPill: document.getElementById("dataSourcePill"),
  playerName: document.getElementById("playerName"),
  playerMeta: document.getElementById("playerMeta"),
  durabilityValue: document.getElementById("durabilityValue"),
  summaryText: document.getElementById("summaryText"),
  sourceBadge: document.getElementById("sourceBadge"),
  scoutNote: document.getElementById("scoutNote"),
  sourceNote: document.getElementById("sourceNote"),
  compsCaveat: document.getElementById("compsCaveat"),
  compsBody: document.querySelector("#compsTable tbody"),
  percentileBody: document.querySelector("#percentileTable tbody"),
  strengthsList: document.getElementById("strengthsList"),
  weaknessesList: document.getElementById("weaknessesList"),
  addBtn: document.getElementById("addProspectBtn"),
  dialog: document.getElementById("addProspectDialog"),
  form: document.getElementById("addProspectForm"),
  cancelBtn: document.getElementById("cancelAddProspect"),
};

async function api(path, options) {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

function renderList(filterText = "") {
  const q = filterText.trim().toLowerCase();
  els.list.innerHTML = "";
  const filtered = state.prospects.filter((p) => p.name.toLowerCase().includes(q));
  if (filtered.length === 0) {
    const li = document.createElement("li");
    li.textContent = "No prospects match.";
    li.style.cursor = "default";
    els.list.appendChild(li);
    return;
  }
  for (const p of filtered) {
    const li = document.createElement("li");
    li.dataset.id = p.id;
    li.className = p.id === state.selectedId ? "active" : "";
    const dot = p.data_source === "real" || p.data_source === "live" ? "●" : "○";
    li.innerHTML = `<span>${p.name}</span><span class="pos-tag" title="${SOURCE_LABELS[p.data_source] || "Synthetic demo"}">${dot} ${p.position}</span>`;
    li.addEventListener("click", () => selectProspect(p.id));
    els.list.appendChild(li);
  }
}

async function selectProspect(id) {
  state.selectedId = id;
  renderList(els.search.value);
  els.emptyState.hidden = true;
  els.report.hidden = false;

  const report = await api(`/prospects/${id}/report`);
  renderReport(report);
}

function pct(v) {
  return v === null || v === undefined ? "—" : `${v.toFixed(1)}%`;
}

// Data-provenance badge. This is the one thing on the page that must never
// be ambiguous: "real" is an individually-sourced person (see source_note),
// "live" is pulled fresh from stats.nba.com, "synthetic" is fictional demo
// data and must never be read as a real player.
const SOURCE_LABELS = { real: "Real · sourced", live: "Live NBA stats", synthetic: "Synthetic demo" };
function sourceBadgeHtml(dataSource) {
  const cls = ["real", "live"].includes(dataSource) ? dataSource : "synthetic";
  const label = SOURCE_LABELS[dataSource] || SOURCE_LABELS.synthetic;
  return `<span class="source-badge ${cls}">${label}</span>`;
}

function renderReport(report) {
  const p = report.prospect;
  els.playerName.textContent = p.name;
  els.sourceBadge.innerHTML = sourceBadgeHtml(p.data_source);
  els.playerMeta.textContent = [
    p.position,
    p.team || "Unsigned prospect",
    p.season,
    p.height_in ? `${Math.floor(p.height_in / 12)}'${Math.round(p.height_in % 12)}"` : null,
  ]
    .filter(Boolean)
    .join(" · ");

  if (p.scout_notes) {
    els.scoutNote.textContent = p.scout_notes;
    els.scoutNote.hidden = false;
  } else {
    els.scoutNote.hidden = true;
  }
  if (p.source_note) {
    els.sourceNote.textContent = `Source: ${p.source_note}`;
    els.sourceNote.hidden = false;
  } else {
    els.sourceNote.hidden = true;
  }

  els.durabilityValue.textContent = pct(report.durability_score);
  els.summaryText.textContent = report.summary;

  els.strengthsList.innerHTML = report.strengths.map((s) => `<li>${s}</li>`).join("");
  els.weaknessesList.innerHTML = report.weaknesses.map((s) => `<li>${s}</li>`).join("");

  const anySyntheticComp = report.comparables.some((c) => c.player.data_source === "synthetic");
  els.compsCaveat.textContent = anySyntheticComp
    ? "These comps are drawn from the synthetic demo comp pool (fictional players) — run fetch_live_data.py to compare against real NBA players instead."
    : "";

  els.compsBody.innerHTML = report.comparables
    .map(
      (c) => `<tr>
        <td>${c.player.name}</td>
        <td>${c.player.team || "—"}</td>
        <td>${c.player.pts_pg ?? "—"}</td>
        <td>${c.player.reb_pg ?? "—"}</td>
        <td>${c.player.ast_pg ?? "—"}</td>
        <td>${c.similarity_pct.toFixed(1)}%</td>
        <td class="data-cell">${sourceBadgeHtml(c.player.data_source)}</td>
      </tr>`
    )
    .join("");

  els.percentileBody.innerHTML = report.percentiles
    .map((e) => `<tr><td>${e.label}</td><td>${e.value ?? "—"}</td><td>${pct(e.percentile)}</td></tr>`)
    .join("");

  renderRadar(report.percentiles, p.name);
}

function chartColors() {
  const style = getComputedStyle(document.documentElement);
  return {
    series1: style.getPropertyValue("--series-1").trim() || "#2a78d6",
    series2: style.getPropertyValue("--series-2").trim() || "#eb6834",
    grid: style.getPropertyValue("--gridline").trim() || "#e1e0d9",
    text: style.getPropertyValue("--text-secondary").trim() || "#52514e",
  };
}

function renderRadar(percentiles, prospectName) {
  const ctx = document.getElementById("radarChart");
  const colors = chartColors();
  const labels = percentiles.map((e) => e.label);
  const values = percentiles.map((e) => e.percentile ?? 0);
  const positionAvg = percentiles.map(() => 50); // peer group median, by construction of percentile scoring

  if (state.radarChart) state.radarChart.destroy();
  state.radarChart = new Chart(ctx, {
    type: "radar",
    data: {
      labels,
      datasets: [
        {
          label: prospectName,
          data: values,
          borderColor: colors.series1,
          backgroundColor: colors.series1 + "33",
          pointBackgroundColor: colors.series1,
          borderWidth: 2,
        },
        {
          label: "Position peer median",
          data: positionAvg,
          borderColor: colors.series2,
          backgroundColor: colors.series2 + "1f",
          pointBackgroundColor: colors.series2,
          borderWidth: 2,
          borderDash: [4, 4],
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        r: {
          min: 0,
          max: 100,
          ticks: { display: false },
          grid: { color: colors.grid },
          angleLines: { color: colors.grid },
          pointLabels: { color: colors.text, font: { size: 11 } },
        },
      },
      plugins: {
        legend: { position: "bottom", labels: { color: colors.text, font: { size: 11 } } },
        tooltip: {
          callbacks: {
            label: (item) => `${item.dataset.label}: ${item.formattedValue}th percentile`,
          },
        },
      },
    },
  });
}

// --- Add prospect dialog ----------------------------------------------------
els.addBtn.addEventListener("click", () => els.dialog.showModal());
els.cancelBtn.addEventListener("click", () => els.dialog.close());

els.form.addEventListener("submit", async (e) => {
  const formData = new FormData(els.form);
  const payload = {};
  for (const [key, raw] of formData.entries()) {
    if (raw === "") continue;
    const numericFields = [
      "age", "height_in", "wingspan_in", "weight_lb", "games_played", "minutes_pg",
      "pts_pg", "reb_pg", "ast_pg", "stl_pg", "blk_pg", "tov_pg",
      "fg_pct", "fg3_pct", "ft_pct", "ts_pct", "usage_pct",
    ];
    payload[key] = numericFields.includes(key) ? Number(raw) : raw;
  }

  try {
    const created = await api("/prospects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    els.form.reset();
    await loadProspects();
    selectProspect(created.id);
  } catch (err) {
    alert(`Could not save prospect: ${err.message}`);
    e.preventDefault();
  }
});

els.search.addEventListener("input", () => renderList(els.search.value));

async function loadProspects() {
  state.prospects = await api("/prospects");
  renderList(els.search.value);
}

async function init() {
  try {
    await loadProspects();
    const players = await api("/players");
    const realProspects = state.prospects.filter((p) => p.data_source === "real" || p.data_source === "live").length;
    const proSource = players.length && players.every((p) => p.data_source === "synthetic") ? "synthetic" : "live/real";
    els.dataPill.textContent = state.prospects.length
      ? `${realProspects}/${state.prospects.length} prospects real · ${players.length} comp-pool (${proSource})`
      : "No prospects yet — add one";
    if (state.prospects.length) selectProspect(state.prospects[0].id);
  } catch (err) {
    els.dataPill.textContent = "API unreachable";
    els.emptyState.innerHTML = `<p>Could not reach the API. Is the backend running? (<code>uvicorn backend.app.main:app</code>)<br><span class="muted small">${err.message}</span></p>`;
  }
}

init();
