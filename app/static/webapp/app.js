const tg = window.Telegram?.WebApp;
tg?.ready();
tg?.expand();

const initData = tg?.initData || "";

const state = {
  historyPage: 1,
  historyStatus: "",
  historyTotal: 0,
  pageSize: 20,
};

async function api(path, options = {}) {
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
  return res.json();
}

function toast(message) {
  const el = document.getElementById("toast");
  el.textContent = message;
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 2500);
}

function fmtDate(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" }) +
    " " + d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
}

function poTotal(po) {
  return po.items.reduce((sum, it) => sum + it.qty * it.price, 0).toFixed(2);
}

function poCard(po) {
  const div = document.createElement("div");
  div.className = "po-card";
  div.innerHTML = `
    <div class="po-card-main">
      <div class="po-card-title">${po.po_id} — ${po.supplier_name}</div>
      <div class="po-card-sub">${fmtDate(po.created_at)} · $${poTotal(po)}</div>
    </div>
    <span class="badge ${po.status}">${po.status}</span>
  `;
  div.addEventListener("click", () => openDetail(po.id));
  return div;
}

function renderList(container, items, emptyMessage) {
  container.innerHTML = "";
  if (!items.length) {
    container.innerHTML = `<div class="empty-state">${emptyMessage}</div>`;
    return;
  }
  items.forEach((po) => container.appendChild(poCard(po)));
}

async function loadDashboard() {
  const data = await api("/api/webapp/dashboard");
  const statsEl = document.getElementById("stats");
  const labels = { pending: "Pending", dispatched: "In Progress", completed: "Completed", failed: "Failed" };
  statsEl.innerHTML = Object.entries(labels)
    .map(
      ([key, label]) => `
      <div class="stat-card">
        <div class="stat-value">${data.counts[key] ?? 0}</div>
        <div class="stat-label">${label}</div>
      </div>`
    )
    .join("");
  renderList(document.getElementById("recent-list"), data.recent, "No purchase orders yet — send one to the bot.");
}

async function loadHistory() {
  const q = new URLSearchParams({
    page: state.historyPage,
    page_size: state.pageSize,
  });
  if (state.historyStatus) q.set("status", state.historyStatus);

  const data = await api(`/api/webapp/history?${q.toString()}`);
  state.historyTotal = data.total;
  renderList(document.getElementById("history-list"), data.items, "No orders match this filter.");

  const pager = document.getElementById("history-pager");
  const totalPages = Math.max(1, Math.ceil(data.total / state.pageSize));
  pager.innerHTML = `
    <button id="prev-page" ${state.historyPage <= 1 ? "disabled" : ""}>← Prev</button>
    <span style="align-self:center;color:var(--hint);font-size:13px;">${state.historyPage} / ${totalPages}</span>
    <button id="next-page" ${state.historyPage >= totalPages ? "disabled" : ""}>Next →</button>
  `;
  document.getElementById("prev-page").onclick = () => {
    state.historyPage -= 1;
    loadHistory();
  };
  document.getElementById("next-page").onclick = () => {
    state.historyPage += 1;
    loadHistory();
  };
}

function switchTab(tab) {
  document.querySelectorAll(".tab").forEach((btn) => btn.classList.toggle("active", btn.dataset.tab === tab));
  document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.toggle("active", panel.id === `tab-${tab}`));
  if (tab === "dashboard") loadDashboard().catch((e) => toast(e.message));
  if (tab === "history") loadHistory().catch((e) => toast(e.message));
}

document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => switchTab(btn.dataset.tab));
});

document.querySelectorAll("#status-filters .chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    document.querySelectorAll("#status-filters .chip").forEach((c) => c.classList.remove("active"));
    chip.classList.add("active");
    state.historyStatus = chip.dataset.status;
    state.historyPage = 1;
    loadHistory().catch((e) => toast(e.message));
  });
});

// --- Detail / regenerate sheet ---

let currentItems = [];
let currentPoId = null;

function itemRow(item, idx) {
  return `
    <div class="item-row" data-idx="${idx}">
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
  currentItems = po.items.map((i) => ({ ...i }));
  currentPoId = po.id;

  const editable = po.status === "failed" || po.status === "completed";

  const body = document.getElementById("sheet-body");
  body.innerHTML = `
    <div class="detail-title">${po.po_id} — ${po.supplier_name}</div>
    <div class="detail-sub">
      <span class="badge ${po.status}">${po.status}</span>
      &nbsp;·&nbsp; ${fmtDate(po.created_at)} &nbsp;·&nbsp; Total $${poTotal(po)}
    </div>
    ${po.error_message ? `<div class="error-text">${escapeAttr(po.error_message)}</div>` : ""}
    ${po.file_url ? `<a class="link-btn" href="${po.file_url}" target="_blank">📄 Open generated document</a>` : ""}

    <div class="row-labels"><span>Item</span><span>Qty</span><span>Unit</span><span>Price</span></div>
    <div id="items-editor">${po.items.map(itemRow).join("")}</div>

    ${editable ? `
      <div class="actions">
        <button class="btn btn-secondary" id="add-item">+ Add item</button>
        <button class="btn btn-primary" id="regenerate-btn">🔁 Regenerate</button>
      </div>
    ` : `<div class="detail-sub" style="margin-top:14px;">This order is ${po.status}; it can be edited once it completes or fails.</div>`}
  `;

  if (editable) {
    document.getElementById("add-item").onclick = () => {
      currentItems.push({ department: "Kitchen", name: "", qty: 1, packing: "", price: 0 });
      document.getElementById("items-editor").innerHTML = currentItems.map(itemRow).join("");
    };
    document.getElementById("regenerate-btn").onclick = submitRegenerate;
  }

  document.getElementById("detail-sheet").classList.remove("hidden");
}

async function submitRegenerate() {
  const rows = document.querySelectorAll("#items-editor .item-row");
  const items = Array.from(rows).map((row) => ({
    department: "Kitchen",
    name: row.querySelector(".f-name").value.trim(),
    qty: parseFloat(row.querySelector(".f-qty").value) || 0,
    packing: row.querySelector(".f-packing").value.trim(),
    price: parseFloat(row.querySelector(".f-price").value) || 0,
  })).filter((i) => i.name && i.qty > 0);

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
    toast("Regeneration triggered ✅");
    closeSheet();
    loadHistory().catch(() => {});
    loadDashboard().catch(() => {});
  } catch (e) {
    toast(e.message);
    btn.disabled = false;
    btn.textContent = "🔁 Regenerate";
  }
}

async function openDetail(id) {
  try {
    const po = await api(`/api/webapp/po/${id}`);
    renderDetail(po);
  } catch (e) {
    toast(e.message);
  }
}

function closeSheet() {
  document.getElementById("detail-sheet").classList.add("hidden");
}

document.getElementById("sheet-close").addEventListener("click", closeSheet);
document.getElementById("detail-sheet").addEventListener("click", (e) => {
  if (e.target.id === "detail-sheet") closeSheet();
});

// Initial load
loadDashboard().catch((e) => toast(e.message));
