const tg = window.Telegram?.WebApp;
tg?.ready();
tg?.expand();
tg?.setHeaderColor?.("secondary_bg_color");
tg?.disableVerticalSwipes?.();

const initData = tg?.initData || "";
const haptic = (type = "light") => tg?.HapticFeedback?.impactOccurred?.(type);

// ---------- i18n ----------

const STRINGS = {
  en: {
    subtitle: "Purchase order dashboard",
    greeting: (name) => `Hi, ${name} 👋`,
    tab_dashboard: "Dashboard",
    tab_history: "History",
    recent_orders: "Recent Orders",
    filter_all: "All",
    status_pending: "Pending",
    status_dispatched: "In Progress",
    status_completed: "Completed",
    status_failed: "Failed",
    empty_dashboard: "No purchase orders yet — send one to the bot.",
    empty_history: "No orders match this filter.",
    prev: "← Prev",
    next: "Next →",
    total: "Total",
    open_document: "📄 Open generated document",
    not_editable: (status) => `This order is ${status}; it can be edited once it completes or fails.`,
    add_item: "+ Add item",
    regenerate: "🔁 Regenerate",
    sending: "Sending…",
    regenerate_success: "Regeneration triggered ✅",
    add_valid_item: "Add at least one valid item",
    no_order_loaded: "No order loaded",
    po_id_label: "PO ID",
    supplier_label: "Supplier",
    supplier_placeholder: "Supplier name",
    col_item: "Item",
    col_qty: "Qty",
    col_unit: "Unit",
    col_price: "Price",
    delete: "Delete",
    delete_confirm_title: "Delete purchase order?",
    delete_confirm_body: (id) => `"${id}" will be permanently deleted. This can't be undone.`,
    deleting: "Deleting…",
    delete_success: "Order deleted",
    delete_failed: "Couldn't delete order",
    add_to_home: "Add to Home Screen",
    add_to_home_success: "Added to Home Screen ✅",
    add_to_home_failed: "Couldn't add to Home Screen",
  },
  km: {
    subtitle: "ផ្ទាំងគ្រប់គ្រងបញ្ជាទិញ",
    greeting: (name) => `សួស្តី ${name} 👋`,
    tab_dashboard: "ផ្ទាំងគ្រប់គ្រង",
    tab_history: "ប្រវត្តិ",
    recent_orders: "បញ្ជាទិញថ្មីៗ",
    filter_all: "ទាំងអស់",
    status_pending: "កំពុងរង់ចាំ",
    status_dispatched: "កំពុងដំណើរការ",
    status_completed: "បានបញ្ចប់",
    status_failed: "បរាជ័យ",
    empty_dashboard: "មិនទាន់មានបញ្ជាទិញនៅឡើយទេ — សូមផ្ញើមួយទៅកាន់ bot",
    empty_history: "គ្មានបញ្ជាទិញត្រូវនឹងតម្រងនេះទេ",
    prev: "← មុន",
    next: "បន្ទាប់ →",
    total: "សរុប",
    open_document: "📄 បើកឯកសារដែលបានបង្កើត",
    not_editable: (status) => `បញ្ជាទិញនេះស្ថិតក្នុងស្ថានភាព ${status}; អាចកែសម្រួលបានបន្ទាប់ពីវាបញ្ចប់ ឬបរាជ័យ`,
    add_item: "+ បន្ថែមទំនិញ",
    regenerate: "🔁 បង្កើតឡើងវិញ",
    sending: "កំពុងផ្ញើ…",
    regenerate_success: "បានបញ្ជូនសំណើបង្កើតឡើងវិញ ✅",
    add_valid_item: "សូមបន្ថែមទំនិញត្រឹមត្រូវយ៉ាងហោចណាស់មួយ",
    no_order_loaded: "មិនមានបញ្ជាទិញផ្ទុក",
    po_id_label: "លេខបញ្ជាទិញ",
    supplier_label: "អ្នកផ្គត់ផ្គង់",
    supplier_placeholder: "ឈ្មោះអ្នកផ្គត់ផ្គង់",
    col_item: "ទំនិញ",
    col_qty: "បរិមាណ",
    col_unit: "ឯកតា",
    col_price: "តម្លៃ",
    delete: "លុប",
    delete_confirm_title: "លុបបញ្ជាទិញនេះ?",
    delete_confirm_body: (id) => `"${id}" នឹងត្រូវបានលុបជាអចិន្ត្រៃយ៍ ។ សកម្មភាពនេះមិនអាចត្រឡប់វិញបានទេ។`,
    deleting: "កំពុងលុប…",
    delete_success: "បានលុបបញ្ជាទិញ",
    delete_failed: "មិនអាចលុបបញ្ជាទិញបានទេ",
    add_to_home: "បន្ថែមទៅអេក្រង់ដើម",
    add_to_home_success: "បានបន្ថែមទៅអេក្រង់ដើម ✅",
    add_to_home_failed: "មិនអាចបន្ថែមទៅអេក្រង់ដើមបានទេ",
  },
};

const STATUS_KEY = { pending: "status_pending", dispatched: "status_dispatched", completed: "status_completed", failed: "status_failed" };

const i18nState = {
  lang: localStorage.getItem("po_lang") || (tg?.initDataUnsafe?.user?.language_code === "km" ? "km" : "en"),
};

function t(key, ...args) {
  const entry = STRINGS[i18nState.lang][key] ?? STRINGS.en[key];
  return typeof entry === "function" ? entry(...args) : entry;
}

function applyStaticTranslations() {
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.dataset.i18n;
    el.textContent = t(key);
  });
  document.getElementById("user-sub").textContent = t("subtitle");
  document.documentElement.lang = i18nState.lang === "km" ? "km" : "en";
  document.getElementById("lang-toggle").textContent = i18nState.lang === "km" ? "KH" : "EN";
  document.getElementById("home-toggle").title = t("add_to_home");
}

function setLanguage(lang) {
  i18nState.lang = lang;
  localStorage.setItem("po_lang", lang);
  applyStaticTranslations();
  const activePanel = document.querySelector(".tab-panel.active")?.id;
  if (activePanel === "tab-dashboard") loadDashboard();
  if (activePanel === "tab-history") loadHistory();
  if (currentPo) renderDetail(currentPo);
}

document.getElementById("lang-toggle").addEventListener("click", () => {
  haptic("light");
  setLanguage(i18nState.lang === "km" ? "en" : "km");
});

// ---------- Theme ----------

const themeState = {
  mode: localStorage.getItem("po_theme") || tg?.colorScheme || "dark",
};

function applyTheme(mode) {
  themeState.mode = mode;
  localStorage.setItem("po_theme", mode);
  document.documentElement.setAttribute("data-theme", mode);
  document.getElementById("theme-toggle").textContent = mode === "light" ? "☀️" : "🌙";
}

document.getElementById("theme-toggle").addEventListener("click", () => {
  haptic("light");
  applyTheme(themeState.mode === "light" ? "dark" : "light");
});

// ---------- Add to Home Screen ----------
// Bot API 8.0+. Lets users pin the Mini App without going through Telegram's
// own "⋮" menu. We feature-detect since older clients won't have the method,
// and hide the button once we know it's already been added.

const homeBtn = document.getElementById("home-toggle");

function initHomeScreenButton() {
  if (!tg || typeof tg.addToHomeScreen !== "function") return; // unsupported client

  const showButton = () => homeBtn.classList.remove("hidden");
  const hideButton = () => homeBtn.classList.add("hidden");

  if (typeof tg.checkHomeScreenStatus === "function") {
    try {
      tg.checkHomeScreenStatus((status) => {
        // status: 'unsupported' | 'unknown' | 'added' | 'missed'
        if (status === "added") hideButton();
        else if (status === "unsupported") hideButton();
        else showButton();
      });
    } catch {
      // Some clients (notably iOS) can't determine status reliably — show
      // the button anyway and let addToHomeScreen itself handle it.
      showButton();
    }
  } else {
    showButton();
  }

  tg.onEvent?.("homeScreenAdded", () => {
    haptic("medium");
    toast(t("add_to_home_success"));
    hideButton();
  });

  tg.onEvent?.("homeScreenChecked", (status) => {
    if (status === "added" || status === "unsupported") hideButton();
  });

  homeBtn.addEventListener("click", () => {
    haptic("light");
    try {
      tg.addToHomeScreen();
    } catch (e) {
      toast(t("add_to_home_failed"));
    }
  });
}

// ---------- App state ----------

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
    if (res.status === 204) return null;
    const text = await res.text();
    return text ? JSON.parse(text) : null;
  } finally {
    setProgress(false);
  }
}

function confirmAction(title, body) {
  return new Promise((resolve) => {
    if (tg?.showConfirm) {
      // Telegram's native confirm only takes a single message string.
      tg.showConfirm(`${title}\n\n${body}`, (ok) => resolve(!!ok));
    } else {
      resolve(window.confirm(`${title}\n\n${body}`));
    }
  });
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
  const locale = i18nState.lang === "km" ? "km-KH" : undefined;
  return (
    d.toLocaleDateString(locale, { month: "short", day: "numeric" }) +
    " " +
    d.toLocaleTimeString(locale, { hour: "2-digit", minute: "2-digit" })
  );
}

function poTotal(po) {
  return po.items.reduce((sum, it) => sum + it.qty * it.price, 0).toFixed(2);
}

const STATUS_ICON = { pending: "⏳", dispatched: "🚀", completed: "✅", failed: "❌" };

const REVEAL_WIDTH = 76; // px the card slides to expose the delete action

function poCard(po, delayIndex = 0) {
  const wrapper = document.createElement("div");
  wrapper.className = "po-card-wrapper";
  wrapper.dataset.poId = po.id;
  wrapper.style.animationDelay = `${Math.min(delayIndex, 8) * 35}ms`;

  wrapper.innerHTML = `
    <div class="po-card-delete-action">🗑️</div>
    <div class="po-card">
      <div class="po-card-main">
        <div class="po-card-title">${po.po_id} — ${escapeHtml(po.supplier_name)}</div>
        <div class="po-card-sub">${fmtDate(po.created_at)} · $${poTotal(po)}</div>
      </div>
      <span class="badge ${po.status}">${STATUS_ICON[po.status] || ""} ${t(STATUS_KEY[po.status] || "status_pending")}</span>
    </div>
  `;

  const card = wrapper.querySelector(".po-card");
  const deleteAction = wrapper.querySelector(".po-card-delete-action");
  attachSwipeToDelete(wrapper, card, po);

  deleteAction.addEventListener("click", () => requestDelete(po, wrapper));

  card.addEventListener("click", () => {
    // If the card is currently swiped open, a tap just closes it again —
    // mirrors iOS/Android list behavior instead of opening the detail sheet.
    if (card.classList.contains("swiped")) {
      closeSwipe(card);
      return;
    }
    haptic("light");
    openDetail(po.id);
  });

  return wrapper;
}

function closeSwipe(card) {
  card.classList.remove("swiped");
  card.style.transform = "";
}

function attachSwipeToDelete(wrapper, card, po) {
  let startX = 0;
  let startY = 0;
  let dx = 0;
  let dragging = false;
  let axisLocked = null; // 'x' | 'y' | null

  const onStart = (clientX, clientY) => {
    startX = clientX;
    startY = clientY;
    dx = card.classList.contains("swiped") ? -REVEAL_WIDTH : 0;
    dragging = true;
    axisLocked = null;
    card.classList.add("dragging");
  };

  const onMove = (clientX, clientY) => {
    if (!dragging) return;
    const deltaX = clientX - startX;
    const deltaY = clientY - startY;

    if (axisLocked === null) {
      if (Math.abs(deltaX) < 6 && Math.abs(deltaY) < 6) return;
      axisLocked = Math.abs(deltaX) > Math.abs(deltaY) ? "x" : "y";
    }
    if (axisLocked === "y") return; // let the page scroll vertically

    const base = card.classList.contains("swiped") ? -REVEAL_WIDTH : 0;
    dx = Math.min(0, Math.max(-REVEAL_WIDTH - 20, base + deltaX));
    card.style.transform = `translateX(${dx}px)`;
  };

  const onEnd = () => {
    if (!dragging) return;
    dragging = false;
    card.classList.remove("dragging");
    if (axisLocked !== "x") return;

    if (dx < -REVEAL_WIDTH / 2) {
      card.classList.add("swiped");
      card.style.transform = `translateX(-${REVEAL_WIDTH}px)`;
      haptic("light");
    } else {
      closeSwipe(card);
    }
  };

  card.addEventListener("touchstart", (e) => onStart(e.touches[0].clientX, e.touches[0].clientY), { passive: true });
  card.addEventListener("touchmove", (e) => onMove(e.touches[0].clientX, e.touches[0].clientY), { passive: true });
  card.addEventListener("touchend", onEnd);
  card.addEventListener("touchcancel", onEnd);
}

async function requestDelete(po, wrapper) {
  haptic("medium");
  const ok = await confirmAction(t("delete_confirm_title"), t("delete_confirm_body", po.po_id));
  if (!ok) {
    const card = wrapper.querySelector(".po-card");
    if (card) closeSwipe(card);
    return;
  }

  try {
    await api(`/api/webapp/po/${po.id}`, { method: "DELETE" });
    haptic("medium");
    toast(t("delete_success"));
    // Smooth iOS-style collapse, then refresh whichever data is on screen.
    wrapper.classList.add("removing");
    wrapper.addEventListener(
      "animationend",
      () => {
        wrapper.remove();
        loadDashboard();
        if (document.getElementById("tab-history").classList.contains("active")) loadHistory();
      },
      { once: true }
    );
  } catch (e) {
    haptic("heavy");
    toast(e.message || t("delete_failed"));
    const card = wrapper.querySelector(".po-card");
    if (card) closeSwipe(card);
  }
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

async function loadMe() {
  try {
    const me = await api("/api/webapp/me");
    const header = document.getElementById("user-header");
    const greeting = document.getElementById("user-greeting");
    const avatar = document.getElementById("user-avatar");
    greeting.textContent = t("greeting", me.first_name || (i18nState.lang === "km" ? "អ្នក" : "there"));
    if (me.photo_url) {
      avatar.src = me.photo_url;
      avatar.classList.remove("hidden");
    }
    header.classList.remove("hidden");
  } catch (e) {
    // Non-critical — dashboard still works without the greeting.
  }
}

async function loadDashboard() {
  const statsEl = document.getElementById("stats");
  const recentEl = document.getElementById("recent-list");
  renderSkeleton(statsEl, 4, "skeleton-stat");
  renderSkeleton(recentEl, 3, "skeleton-card");

  try {
    const data = await api("/api/webapp/dashboard");
    const order = ["pending", "dispatched", "completed", "failed"];
    statsEl.innerHTML = order
      .map(
        (key) => `
        <div class="stat-card ${key}">
          <div class="stat-value">${data.counts[key] ?? 0}</div>
          <div class="stat-label">${STATUS_ICON[key]} ${t(STATUS_KEY[key])}</div>
        </div>`
      )
      .join("");
    renderList(recentEl, data.recent, t("empty_dashboard"), "🧾");
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
    renderList(listEl, data.items, t("empty_history"), "🔎");

    const totalPages = Math.max(1, Math.ceil(data.total / state.pageSize));
    pagerEl.innerHTML = `
      <button id="prev-page" ${state.historyPage <= 1 ? "disabled" : ""}>${t("prev")}</button>
      <span style="color:var(--hint);font-size:13px;">${state.historyPage} / ${totalPages}</span>
      <button id="next-page" ${state.historyPage >= totalPages ? "disabled" : ""}>${t("next")}</button>
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
let currentPo = null;

function itemRow(item) {
  return `
    <div class="item-row">
      <input class="f-name" value="${escapeAttr(item.name)}" placeholder="${t("col_item")}" />
      <input class="f-qty" type="number" step="any" value="${item.qty}" placeholder="${t("col_qty")}" />
      <input class="f-packing" value="${escapeAttr(item.packing || "")}" placeholder="${t("col_unit")}" />
      <input class="f-price" type="number" step="any" value="${item.price}" placeholder="${t("col_price")}" />
    </div>
  `;
}

function escapeAttr(s) {
  return String(s).replace(/"/g, "&quot;");
}

function renderDetail(po) {
  currentPoId = po.id;
  currentPo = po;
  const editable = po.status === "failed" || po.status === "completed";

  const body = document.getElementById("sheet-body");
  body.innerHTML = `
    <div class="detail-title">${po.po_id} — ${escapeHtml(po.supplier_name)}</div>
    <div class="detail-sub">
      <span class="badge ${po.status}">${STATUS_ICON[po.status] || ""} ${t(STATUS_KEY[po.status] || "status_pending")}</span>
      <span>${fmtDate(po.created_at)}</span>
      <span>· ${t("total")} $${poTotal(po)}</span>
    </div>
    ${po.error_message ? `<div class="error-text">${escapeHtml(po.error_message)}</div>` : ""}
    ${po.file_url ? `<a class="link-btn" href="${po.file_url}" target="_blank">${t("open_document")}</a>` : ""}

    ${
      editable
        ? `
      <div class="row-labels"><span>${t("po_id_label")}</span><span style="grid-column: span 3;">${t("supplier_label")}</span></div>
      <div class="header-edit-row">
        <input id="edit-po-id" value="${escapeAttr(po.po_id)}" placeholder="${t("po_id_label")}" />
        <input id="edit-supplier" value="${escapeAttr(po.supplier_name)}" placeholder="${t("supplier_placeholder")}" />
      </div>
    `
        : ""
    }

    <div class="row-labels"><span>${t("col_item")}</span><span>${t("col_qty")}</span><span>${t("col_unit")}</span><span>${t("col_price")}</span></div>
    <div id="items-editor">${po.items.map(itemRow).join("")}</div>

    ${
      editable
        ? `
      <div class="actions">
        <button class="btn btn-secondary" id="add-item">${t("add_item")}</button>
        <button class="btn btn-primary" id="regenerate-btn">${t("regenerate")}</button>
        <button class="btn btn-danger" id="delete-po-btn" title="${t("delete")}">🗑️</button>
      </div>
    `
        : `
      <div class="detail-sub" style="margin-top:14px;">${t("not_editable", t(STATUS_KEY[po.status] || "status_pending"))}</div>
      <div class="actions">
        <button class="btn btn-danger" id="delete-po-btn">🗑️ ${t("delete")}</button>
      </div>
    `
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
  document.getElementById("delete-po-btn").onclick = submitDeleteFromSheet;

  document.getElementById("detail-sheet").classList.remove("hidden");
}

async function submitDeleteFromSheet() {
  if (!currentPo) {
    toast(t("no_order_loaded"));
    return;
  }
  haptic("medium");
  const ok = await confirmAction(t("delete_confirm_title"), t("delete_confirm_body", currentPo.po_id));
  if (!ok) return;

  const btn = document.getElementById("delete-po-btn");
  if (btn) {
    btn.disabled = true;
    btn.textContent = t("deleting");
  }

  try {
    await api(`/api/webapp/po/${currentPoId}`, { method: "DELETE" });
    haptic("medium");
    toast(t("delete_success"));
    closeSheet();
    loadDashboard();
    if (document.getElementById("tab-history").classList.contains("active")) loadHistory();
  } catch (e) {
    haptic("heavy");
    toast(e.message || t("delete_failed"));
    if (btn) {
      btn.disabled = false;
      btn.textContent = `🗑️ ${t("delete")}`;
    }
  }
}

async function submitRegenerate() {
  if (!currentPo) {
    toast(t("no_order_loaded"));
    return;
  }

  const rows = document.querySelectorAll("#items-editor .item-row");
  const items = Array.from(rows)
    .map((row, i) => ({
      department: currentPo.items[i]?.department || "Kitchen",
      name: row.querySelector(".f-name").value.trim(),
      qty: parseFloat(row.querySelector(".f-qty").value) || 0,
      packing: row.querySelector(".f-packing").value.trim(),
      price: parseFloat(row.querySelector(".f-price").value) || 0,
    }))
    .filter((i) => i.name && i.qty > 0);

  if (!items.length) {
    toast(t("add_valid_item"));
    return;
  }

  const btn = document.getElementById("regenerate-btn");
  btn.disabled = true;
  btn.textContent = t("sending");

  const supplierName =
    document.getElementById("edit-supplier")?.value.trim() || currentPo.supplier_name;
  const poId =
    document.getElementById("edit-po-id")?.value.trim() || currentPo.po_id;

  try {
    await api(`/api/webapp/po/${currentPoId}/regenerate`, {
      method: "POST",
      body: JSON.stringify({ po_id: poId, supplier_name: supplierName, items }),
    });
    haptic("medium");
    toast(t("regenerate_success"));
    closeSheet();
    loadHistory();
    loadDashboard();
  } catch (e) {
    haptic("heavy");
    toast(e.message);
    btn.disabled = false;
    btn.textContent = t("regenerate");
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
  currentPo = null;
  currentPoId = null;
}

document.getElementById("sheet-close").addEventListener("click", () => {
  haptic("light");
  closeSheet();
});
document.querySelector("#detail-sheet .sheet-backdrop").addEventListener("click", closeSheet);

// ---------- Init ----------

applyTheme(themeState.mode);
applyStaticTranslations();
initHomeScreenButton();
loadMe();
loadDashboard();