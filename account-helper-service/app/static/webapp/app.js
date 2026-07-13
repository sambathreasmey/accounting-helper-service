const tg = window.Telegram?.WebApp;
tg?.ready();
tg?.expand();
tg?.setHeaderColor?.("secondary_bg_color");

const initData = tg?.initData || "";
const haptic = (type = "light") => tg?.HapticFeedback?.impactOccurred?.(type);

const state = {
  historyPage: 1,
  historyStatus: "",
  historyTotal: 0,
  pageSize: 20,
};

let activeRequests = 0;

function setProgress(active) {
  activeRequests = Math.max(0, activeRequests + (active ? 1 : -1));
  document.getElementById("progress-bar").classList.toggle("active", activeRequests > 0);
}

async function api(path, options = {}) {
  setProgress(true);
  try {
    const res = await fetch(path, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        "X-Telegram-Init-Data": initData,
        ...(options.headers || {}),
      },
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Request failed (${res.status})`);
    }
    return await res.json();
  } finally {
    setProgress(false);
  }
}

function toast(message) {
  const el = document.getElementById("toast");
  el.textContent = message;
  el.classList.remove("hidden");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => el.classList.add("hidden"), 2500);
}

function fmtDate(iso) {
  const d = new Date(iso);
  return (
    d.toLocaleDateString(undefined, { month: "short", day: "numeric" }) +
    " " +
    d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })
  );
}

function poTotal(po) {
  return po.items.reduce((sum, it) => sum + it.qty * it.price, 0).toFixed(2);
}

const STATUS_ICON = { pending: "⏳", dispatched: "🚀", completed: "✅", failed: "❌" };

function poCard(po, delayIndex = 0) {
  const div = document.createElement("div");
  div.className = "po-card";
  div.style.animationDelay = `${Math.min(delayIndex, 8) * 35}ms`;
  div.innerHTML = `
    <div class="po-card-main">
      <div class="po-card-title">${po.po_id} — ${escapeHtml(po.supplier_name)}</div>
      <div class="po-card-sub">${fmtDate(po.created_at)} · $${poTotal(po)}</div>
    </div>
    <span class="badge ${po.status}">${STATUS_ICON[po.status] || ""} ${po.status}</span>
  `;
  div.addEventListener("click", () => {
    haptic("light");
    openDetail(po.id);
  });
  return div;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

function renderSkeleton(container, count, className) {
  container.innerHTML = Array.from({ length: count })
    .map(() => `<div class="skeleton ${className}"></div>`)
    .join("");
}

function renderList(container, items, emptyMessage, emptyIcon = "📭") {
  container.innerHTML = "";
  if (!items.length) {
    container.innerHTML = `<div class="empty-state"><span class="empty-icon">${emptyIcon}</span>${emptyMessage}</div>`;
    return;
  }
  items.forEach((po, i) => container.appendChild(poCard(po, i)));
}

async function loadDashboard() {
  const statsEl = document.getElementById("stats");
  const recentEl = document.getElementById("recent-list");
  renderSkeleton(statsEl, 4, "skeleton-stat");
  renderSkeleton(recentEl, 3, "skeleton-card");

  try {
    const data = await api("/api/webapp/dashboard");
    const labels = { pending: "Pending", dispatched: "In Progress", completed: "Completed", failed: "Failed" };
    statsEl.innerHTML = Object.entries(labels)
      .map(
        ([key, label]) => `
        <div class="stat-card ${key}">
          <div class="stat-value">${data.counts[key] ?? 0}</div>
          <div class="stat-label">${STATUS_ICON[key]} ${label}</div>
        </div>`
      )
      .join("");
    renderList(recentEl, data.recent, "No purchase orders yet — send one to the bot.", "🧾");
  } catch (e) {
    statsEl.innerHTML = "";
    recentEl.innerHTML = `<div class="empty-state"><span class="empty-icon">⚠️</span>${escapeHtml(e.message)}</div>`;
  }
}

async function loadHistory() {
  const listEl = document.getElementById("history-list");
  const pagerEl = document.getElementById("history-pager");
  renderSkeleton(listEl, 5, "skeleton-card");
  pagerEl.innerHTML = "";

  const q = new URLSearchParams({ page: state.historyPage, page_size: state.pageSize });
  if (state.historyStatus) q.set("status", state.historyStatus);

  try {
    const data = await api(`/api/webapp/history?${q.toString()}`);
    state.historyTotal = data.total;
    renderList(listEl, data.items, "No orders match this filter.", "🔎");

    const totalPages = Math.max(1, Math.ceil(data.total / state.pageSize));
    pagerEl.innerHTML = `
      <button id="prev-page" ${state.historyPage <= 1 ? "disabled" : ""}>← Prev</button>
      <span style="color:var(--hint);font-size:13px;">${state.historyPage} / ${totalPages}</span>
      <button id="next-page" ${state.historyPage >= totalPages ? "disabled" : ""}>Next →</button>
    `;
    document.getElementById("prev-page").onclick = () => {
      haptic("light");
      state.historyPage -= 1;
      loadHistory();
    };
    document.getElementById("next-page").onclick = () => {
      haptic("light");
      state.historyPage += 1;
      loadHistory();
    };
  } catch (e) {
    listEl.innerHTML = `<div class="empty-state"><span class="empty-icon">⚠️</span>${escapeHtml(e.message)}</div>`;
  }
}

function switchTab(tab) {
  haptic("light");
  document.querySelectorAll(".tab").forEach((btn) => btn.classList.toggle("active", btn.dataset.tab === tab));
  document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.toggle("active", panel.id === `tab-${tab}`));
  if (tab === "dashboard") loadDashboard();
  if (tab === "history") loadHistory();
}

document.querySelectorAll(".tab").forEach((btn) => btn.addEventListener("click", () => switchTab(btn.dataset.tab)));

document.querySelectorAll("#status-filters .chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    haptic("light");
    document.querySelectorAll("#status-filters .chip").forEach((c) => c.classList.remove("active"));
    chip.classList.add("active");
    state.historyStatus = chip.dataset.status;
    state.historyPage = 1;
    loadHistory();
  });
});

// --- Detail / regenerate sheet ---

let currentPoId = null;

function itemRow(item) {
  return `
    <div class="item-row">
      <input class="f-name" value="${escapeAttr(item.name)}" placeholder="Item" />
      <input class="f-qty" type="number" step="any" value="${item.qty}" placeholder="Qty" />
      <input class="f-packing" value="${escapeAttr(item.packing || "")}" placeholder="Unit" />
      <input class="f-price" type="number" step="any" value="${item.price}" placeholder="Price" />
    </div>
  `;
}

function escapeAttr(s) {
  return String(s).replace(/"/g, "&quot;");
}

function renderDetail(po) {
  currentPoId = po.id;
  const editable = po.status === "failed" || po.status === "completed";

  const body = document.getElementById("sheet-body");
  body.innerHTML = `
    <div class="detail-title">${po.po_id} — ${escapeHtml(po.supplier_name)}</div>
    <div class="detail-sub">
      <span class="badge ${po.status}">${STATUS_ICON[po.status] || ""} ${po.status}</span>
      <span>${fmtDate(po.created_at)}</span>
      <span>· Total $${poTotal(po)}</span>
    </div>
    ${po.error_message ? `<div class="error-text">${escapeHtml(po.error_message)}</div>` : ""}
    ${po.file_url ? `<a class="link-btn" href="${po.file_url}" target="_blank">📄 Open generated document</a>` : ""}

    <div class="row-labels"><span>Item</span><span>Qty</span><span>Unit</span><span>Price</span></div>
    <div id="items-editor">${po.items.map(itemRow).join("")}</div>

    ${
      editable
        ? `
      <div class="actions">
        <button class="btn btn-secondary" id="add-item">+ Add item</button>
        <button class="btn btn-primary" id="regenerate-btn">🔁 Regenerate</button>
      </div>
    `
        : `<div class="detail-sub" style="margin-top:14px;">This order is ${po.status}; it can be edited once it completes or fails.</div>`
    }
  `;

  if (editable) {
    document.getElementById("add-item").onclick = () => {
      haptic("light");
      const editor = document.getElementById("items-editor");
      editor.insertAdjacentHTML("beforeend", itemRow({ name: "", qty: 1, packing: "", price: 0 }));
    };
    document.getElementById("regenerate-btn").onclick = submitRegenerate;
  }

  document.getElementById("detail-sheet").classList.remove("hidden");
}

async function submitRegenerate() {
  const rows = document.querySelectorAll("#items-editor .item-row");
  const items = Array.from(rows)
    .map((row) => ({
      department: "Kitchen",
      name: row.querySelector(".f-name").value.trim(),
      qty: parseFloat(row.querySelector(".f-qty").value) || 0,
      packing: row.querySelector(".f-packing").value.trim(),
      price: parseFloat(row.querySelector(".f-price").value) || 0,
    }))
    .filter((i) => i.name && i.qty > 0);

  if (!items.length) {
    toast("Add at least one valid item");
    return;
  }

  const btn = document.getElementById("regenerate-btn");
  btn.disabled = true;
  btn.textContent = "Sending…";

  try {
    const supplierEl = document.querySelector(".detail-title").textContent.split("—")[1]?.trim();
    await api(`/api/webapp/po/${currentPoId}/regenerate`, {
      method: "POST",
      body: JSON.stringify({ supplier_name: supplierEl || "Unknown", items }),
    });
    haptic("medium");
    toast("Regeneration triggered ✅");
    closeSheet();
    loadHistory();
    loadDashboard();
  } catch (e) {
    haptic("heavy");
    toast(e.message);
    btn.disabled = false;
    btn.textContent = "🔁 Regenerate";
  }
}

async function openDetail(id) {
  const sheet = document.getElementById("detail-sheet");
  const body = document.getElementById("sheet-body");
  sheet.classList.remove("hidden");
  body.innerHTML = `
    <div class="skeleton" style="height:22px;width:60%;margin-bottom:8px;"></div>
    <div class="skeleton" style="height:14px;width:40%;margin-bottom:20px;"></div>
    <div class="skeleton skeleton-card" style="margin-bottom:8px;"></div>
    <div class="skeleton skeleton-card"></div>
  `;
  try {
    const po = await api(`/api/webapp/po/${id}`);
    renderDetail(po);
  } catch (e) {
    toast(e.message);
    closeSheet();
  }
}

function closeSheet() {
  document.getElementById("detail-sheet").classList.add("hidden");
}

document.getElementById("sheet-close").addEventListener("click", () => {
  haptic("light");
  closeSheet();
});
document.querySelector("#detail-sheet .sheet-backdrop").addEventListener("click", closeSheet);

// Initial load
loadDashboard();
