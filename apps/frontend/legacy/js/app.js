/* ==========================================================================
   EduRisk AI — Frontend Application Controller
   Personalized Learning Recommendation System (HCO-VNLS + LightGBM)
   ========================================================================== */
"use strict";

/* ---------- 1. Cấu hình 17 trường đặc trưng (Single Source of Truth) ----------
 * Tên cột PHẢI khớp 100% với mô hình LightGBM đã huấn luyện. */
const FIELDS = [
  // Nhóm: Thông tin cá nhân & đăng ký
  { key: "code_module", group: "info", label: "Mã học phần", hint: "code_module", type: "select",
    options: ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF", "GGG"], default: "BBB" },
  { key: "gender", group: "info", label: "Giới tính", hint: "gender", type: "select",
    options: ["F", "M"], default: "M" },
  { key: "highest_education", group: "info", label: "Học vấn cao nhất", hint: "highest_education", type: "select",
    options: ["A Level or Equivalent", "HE Qualification", "Lower Than A Level", "No Formal quals", "Post Graduate Qualification"],
    default: "A Level or Equivalent" },
  { key: "age_band", group: "info", label: "Nhóm độ tuổi", hint: "age_band", type: "select",
    options: ["0-35", "35-55", "55<="], default: "0-35" },
  { key: "studied_credits", group: "info", label: "Số tín chỉ đăng ký", hint: "studied_credits", type: "number",
    default: 60, step: 5, min: 0 },
  { key: "date_registration", group: "info", label: "Ngày đăng ký môn", hint: "date_registration (âm = trước khai giảng)", type: "number",
    default: -10, step: 1 },

  // Nhóm: Hoạt động học tập trực tuyến (VLE)
  { key: "total_clicks_to_t", group: "activity", label: "Tổng lượt click VLE", hint: "total_clicks_to_t", type: "number",
    default: 1200, step: 10, min: 0 },
  { key: "clicks_resource_to_t", group: "activity", label: "Click đọc tài liệu", hint: "clicks_resource_to_t", type: "number",
    default: 350, step: 10, min: 0 },
  { key: "clicks_url_to_t", group: "activity", label: "Click liên kết ngoài", hint: "clicks_url_to_t", type: "number",
    default: 180, step: 10, min: 0 },
  { key: "active_days_to_t", group: "activity", label: "Số ngày có hoạt động", hint: "active_days_to_t", type: "number",
    default: 60, step: 1, min: 0 },
  { key: "active_day_ratio", group: "activity", label: "Tỉ lệ ngày hoạt động", hint: "active_day_ratio (0.0 – 1.0)", type: "number",
    default: 0.5, step: 0.05, min: 0, max: 1 },
  { key: "days_since_last_activity", group: "activity", label: "Số ngày ngưng truy cập", hint: "days_since_last_activity", type: "number",
    default: 5, step: 1, min: 0 },
  { key: "clicks_recent_7", group: "activity", label: "Lượt click trong 7 ngày", hint: "clicks_recent_7", type: "number",
    default: 60, step: 5, min: 0 },
  { key: "clicks_recent_30", group: "activity", label: "Lượt click trong 30 ngày", hint: "clicks_recent_30", type: "number",
    default: 300, step: 10, min: 0 },

  // Nhóm: Đánh giá & Bài kiểm tra
  { key: "assessments_submitted_to_t", group: "assessment", label: "Số bài kiểm tra đã nộp", hint: "assessments_submitted_to_t", type: "number",
    default: 4, step: 1, min: 0 },
  { key: "late_submissions_to_t", group: "assessment", label: "Số bài nộp muộn hạn", hint: "late_submissions_to_t", type: "number",
    default: 1, step: 1, min: 0 },
  { key: "submission_rate", group: "assessment", label: "Tỉ lệ hoàn thành bài", hint: "submission_rate (0.0 – 1.0)", type: "number",
    default: 0.7, step: 0.05, min: 0, max: 1 },
];

/* ---------- 2. Dữ liệu mẫu hồ sơ sinh viên (Presets) ---------- */
const PRESETS = {
  weak: {
    code_module: "BBB", gender: "M", highest_education: "Lower Than A Level", age_band: "0-35",
    studied_credits: 60, date_registration: -5,
    total_clicks_to_t: 120, clicks_resource_to_t: 30, clicks_url_to_t: 10,
    active_days_to_t: 8, active_day_ratio: 0.12,
    days_since_last_activity: 21, clicks_recent_7: 2, clicks_recent_30: 15,
    assessments_submitted_to_t: 1, late_submissions_to_t: 2, submission_rate: 0.2,
  },
  good: {
    code_module: "AAA", gender: "F", highest_education: "Post Graduate Qualification", age_band: "0-35",
    studied_credits: 30, date_registration: -60,
    total_clicks_to_t: 3200, clicks_resource_to_t: 900, clicks_url_to_t: 400,
    active_days_to_t: 120, active_day_ratio: 0.85,
    days_since_last_activity: 1, clicks_recent_7: 180, clicks_recent_30: 700,
    assessments_submitted_to_t: 8, late_submissions_to_t: 0, submission_rate: 0.95,
  },
};

/* ---------- 3. Quản lý State toàn cục ---------- */
const API_BASE_KEY = "edurisk_api_base";
const HISTORY_KEY = "edurisk_history";
const USER_KEY = "edurisk_current_user";
const GAUGE_CIRC = 2 * Math.PI * 54; // 339.29

function getDefaultApiBase() {
  if (window.location.origin && window.location.origin.startsWith("http")) {
    return window.location.origin;
  }
  return "http://127.0.0.1:8000";
}

function normalizeBase(url) {
  return (url || "").trim().replace(/\/+$/, "");
}

const state = {
  apiBase: normalizeBase(localStorage.getItem(API_BASE_KEY) || getDefaultApiBase()),
  history: JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]"),
  user: JSON.parse(localStorage.getItem(USER_KEY) || "null"),
  currentView: "home",
  healthTimer: null,
  lastPing: null,
};

/* ---------- 4. Tiện ích DOM & Toast Notifications ---------- */
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

function showToast(message, type = "info", duration = 3500) {
  const container = $("#toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;

  const iconMap = {
    success: "✅",
    error: "❌",
    warning: "⚠️",
    info: "ℹ️",
  };

  toast.innerHTML = `
    <span class="toast-icon">${iconMap[type] || "ℹ️"}</span>
    <span class="toast-msg">${message}</span>
    <button type="button" class="toast-close" aria-label="Đóng">&times;</button>
  `;

  toast.querySelector(".toast-close").addEventListener("click", () => {
    toast.remove();
  });

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(20px)";
    setTimeout(() => toast.remove(), 250);
  }, duration);
}

/* ---------- 5. SPA Hash Router ---------- */
function initRouter() {
  const handleRoute = () => {
    const hash = window.location.hash.replace(/^#\/?/, "") || "home";
    const validViews = ["home", "dashboard", "about", "contact"];
    const targetView = validViews.includes(hash) ? hash : "home";
    switchView(targetView);
  };

  window.addEventListener("hashchange", handleRoute);

  // Gắn sự kiện chuyển trang cho mọi thẻ data-nav
  document.addEventListener("click", (e) => {
    const trigger = e.target.closest("[data-nav]");
    if (trigger) {
      e.preventDefault();
      const target = trigger.dataset.nav;
      window.location.hash = target;
    }
  });

  handleRoute();
}

function switchView(viewName) {
  state.currentView = viewName;

  // Cập nhật view active
  $$(".page-view").forEach((el) => {
    el.classList.toggle("active", el.id === `view-${viewName}`);
  });

  // Cập nhật nav link active
  $$(".nav-link").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.nav === viewName);
  });

  window.scrollTo({ top: 0, behavior: "smooth" });
}

/* ---------- 6. Render Form Hồ Sơ Sinh Viên ---------- */
function renderForm() {
  for (const f of FIELDS) {
    const wrap = document.createElement("div");
    wrap.className = "field-item";

    const label = document.createElement("label");
    label.htmlFor = `f-${f.key}`;
    label.textContent = f.label;

    const hint = document.createElement("span");
    hint.className = "field-hint";
    hint.textContent = f.hint;

    let input;
    if (f.type === "select") {
      input = document.createElement("select");
      input.id = `f-${f.key}`;
      for (const opt of f.options) {
        const o = document.createElement("option");
        o.value = opt;
        o.textContent = opt;
        input.appendChild(o);
      }
    } else {
      input = document.createElement("input");
      input.type = "number";
      input.id = `f-${f.key}`;
      input.step = f.step ?? 1;
      if (f.min !== undefined) input.min = f.min;
      if (f.max !== undefined) input.max = f.max;
    }
    input.dataset.key = f.key;
    input.value = f.default;

    wrap.append(label, hint, input);
    const container = $(`.field-grid[data-fields="${f.group}"]`);
    if (container) container.appendChild(wrap);
  }
}

function fillForm(values) {
  for (const f of FIELDS) {
    const el = $(`#f-${f.key}`);
    if (!el) continue;
    el.value = values ? values[f.key] : f.default;
  }
}

function collectFeatures() {
  const features = {};
  for (const f of FIELDS) {
    const el = $(`#f-${f.key}`);
    if (!el) continue;
    features[f.key] = f.type === "select" ? el.value : Number(el.value);
  }
  return features;
}

/* ---------- 7. Kiểm tra Health & Ping Backend API ---------- */
async function checkHealth() {
  const pill = $("#backend-status-btn");
  const text = $("#backend-status-text");
  const pingLabel = $("#api-ping-label");
  const sysUrl = $("#sys-server-url");
  const modalBadge = $("#backend-detail-badge");
  const modalModel = $("#backend-model-loaded");

  if (sysUrl) sysUrl.textContent = state.apiBase;

  const startTime = performance.now();
  try {
    const res = await fetch(`${state.apiBase}/api/v1/health`, {
      signal: AbortSignal.timeout(5000),
    });
    const latency = Math.round(performance.now() - startTime);
    state.lastPing = latency;

    const data = await res.json();
    if (res.ok && data.status === "ok") {
      if (pill) pill.className = "status-pill status-ok";
      if (text) text.textContent = "Backend: OK · Model đã nạp";
      if (pingLabel) pingLabel.textContent = `Ping: ${latency}ms`;
      if (modalBadge) {
        modalBadge.className = "badge badge-ok";
        modalBadge.textContent = "Kết nối tốt";
      }
      if (modalModel) modalModel.textContent = data.model_loaded ? "Đã nạp sẵn (HCO-VNLS)" : "Chưa nạp";
    } else {
      if (pill) pill.className = "status-pill status-checking";
      if (text) text.textContent = "Backend chạy · Model chưa load";
      if (modalBadge) {
        modalBadge.className = "badge badge-down";
        modalBadge.textContent = "Cần nạp model";
      }
    }
  } catch (err) {
    console.warn("Lỗi kiểm tra Backend Health:", err);
    if (pill) pill.className = "status-pill status-down";
    if (text) text.textContent = "Backend: Không kết nối được";
    if (pingLabel) pingLabel.textContent = "Offline";
    if (modalBadge) {
      modalBadge.className = "badge badge-down";
      modalBadge.textContent = "Mất kết nối";
    }
    if (modalModel) modalModel.textContent = "Không xác định";
  }
}

function startHealthPolling() {
  clearInterval(state.healthTimer);
  checkHealth();
  state.healthTimer = setInterval(checkHealth, 30000);
}

/* ---------- 8. Gọi API Dự đoán ---------- */
async function predict(features) {
  const res = await fetch(`${state.apiBase}/api/v1/predictions/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ features }),
    signal: AbortSignal.timeout(20000),
  });

  if (!res.ok) {
    let detail = `Lỗi HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (res.status === 503) detail = "Model LightGBM chưa sẵn sàng trên backend.";
      else if (res.status === 422 && Array.isArray(body.detail)) {
        const first = body.detail[0];
        detail = `Dữ liệu không hợp lệ ở trường '${(first.loc || []).slice(-1)[0]}': ${first.msg}`;
      } else if (typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch { /* default */ }
    throw new Error(detail);
  }

  return res.json();
}

/* ---------- 9. Hiển thị Kết quả Dự đoán ---------- */
function showResult(data, features) {
  const prob = Number(data.confidence ?? 0);
  const atRisk = data.prediction === 1;

  $("#result-placeholder").classList.add("hidden");
  $("#result-content").classList.remove("hidden");

  // Risk Badge
  const badge = $("#risk-badge");
  badge.className = `risk-badge ${atRisk ? "risk-high" : "risk-low"}`;
  $("#risk-icon").textContent = atRisk ? "⚠️" : "✅";
  $("#risk-label").textContent = atRisk ? "NGUY CƠ CAO (AT RISK)" : "AN TOÀN (ON TRACK)";

  // SVG Gauge
  const gauge = $("#gauge-value");
  gauge.setAttribute("class", `gauge-value ${atRisk ? "high" : "low"}`);
  requestAnimationFrame(() => {
    gauge.style.strokeDashoffset = String(GAUGE_CIRC * (1 - prob));
  });

  const percentStr = (prob * 100).toFixed(1);
  $("#gauge-percent").textContent = `${percentStr}%`;

  // Summary Box
  $("#result-summary").textContent = atRisk
    ? `Mô hình dự đoán sinh viên CÓ nguy cơ rớt hoặc bỏ học với xác suất ${percentStr}% (vượt ngưỡng phân lớp).`
    : `Mô hình dự đoán sinh viên AN TOÀN — xác suất rủi ro chỉ ở mức ${percentStr}%.`;

  // Render Recommendations
  renderRecommendations(atRisk, prob, features);

  // Meta info
  const now = new Date().toLocaleString("vi-VN");
  $("#result-meta").textContent = `Dự đoán lúc ${now} &bull; Máy chủ: ${state.apiBase}`;
}

function renderRecommendations(atRisk, prob, f) {
  const box = $("#recommend-box");
  const list = $("#recommend-list");
  list.innerHTML = "";

  if (!atRisk) {
    if (prob >= 0.3) {
      box.classList.remove("hidden");
      addRecItem(list, "Xác suất rủi ro ở mức trung bình (30–50%) — Cố vấn nên theo dõi định kỳ trong 1–2 tuần tới.");
    } else {
      box.classList.add("hidden");
    }
    return;
  }

  const recs = [];
  if (f.days_since_last_activity >= 14) {
    recs.push(`Sinh viên đã ${f.days_since_last_activity} ngày không truy cập hệ thống — Cần liên hệ trực tiếp qua Email/SĐT ngay.`);
  }
  if (f.active_day_ratio < 0.35) {
    recs.push("Tần suất đăng nhập quá thưa thớt — Hướng dẫn thiết lập thời gian biểu học trực tuyến đều đặn.");
  }
  if (f.assessments_submitted_to_t === 0) {
    recs.push("Chưa nộp bất kỳ bài kiểm tra nào — Cảnh báo deadline và hỗ trợ kỹ thuật nộp bài trên LMS.");
  } else if (f.submission_rate < 0.6 || f.late_submissions_to_t >= 2) {
    recs.push("Tỷ lệ nộp bài thấp hoặc nhiều bài nộp muộn — Cố vấn học tập xem xét gia hạn hợp lý và kèm cặp phương pháp.");
  }
  if (f.clicks_recent_30 > 0 && f.clicks_recent_7 < f.clicks_recent_30 / 10) {
    recs.push("Tương tác trong 7 ngày gần đây sụt giảm đột biến so với tháng trước — Cần can thiệp tâm lý hoặc học thuật.");
  }
  if (f.studied_credits >= 90) {
    recs.push("Khối lượng tín chỉ học kỳ này quá nặng — Tư vấn lộ trình rút bớt học phần hoặc chia nhỏ mục tiêu.");
  }
  if (recs.length === 0) {
    recs.push("Trao đổi thêm với giảng viên phụ trách học phần để tìm hiểu hoàn cảnh cụ thể của sinh viên.");
  }

  for (const r of recs) {
    addRecItem(list, r);
  }
  box.classList.remove("hidden");
}

function addRecItem(list, text) {
  const li = document.createElement("li");
  li.textContent = text;
  list.appendChild(li);
}

/* ---------- 10. Lịch Sử Dự Đoán & Xuất CSV ---------- */
function addHistory(data, features) {
  state.history.unshift({
    time: new Date().toLocaleTimeString("vi-VN"),
    date: new Date().toLocaleDateString("vi-VN"),
    module: features.code_module,
    age: features.age_band,
    credits: features.studied_credits,
    clicks: features.total_clicks_to_t,
    prediction: data.prediction,
    confidence: data.confidence,
  });

  if (state.history.length > 30) state.history.pop();
  localStorage.setItem(HISTORY_KEY, JSON.stringify(state.history));
  renderHistory();
}

function renderHistory(filterText = "") {
  const body = $("#history-body");
  if (!body) return;
  body.innerHTML = "";

  const q = filterText.trim().toLowerCase();
  const items = state.history.filter((h) => {
    if (!q) return true;
    return (
      (h.module && h.module.toLowerCase().includes(q)) ||
      (h.age && h.age.toLowerCase().includes(q))
    );
  });

  if (items.length === 0) {
    body.innerHTML = '<tr class="empty-row"><td colspan="8">Không có bản ghi dự đoán nào phù hợp.</td></tr>';
    return;
  }

  for (let idx = 0; idx < items.length; idx++) {
    const h = items[idx];
    const risk = h.prediction === 1;
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${h.time} <small class="text-muted">${h.date || ""}</small></td>
      <td><strong>${h.module}</strong></td>
      <td>${h.age}</td>
      <td>${h.credits} TC</td>
      <td>${Number(h.clicks || 0).toLocaleString("vi-VN")}</td>
      <td><span class="tag-badge ${risk ? "high" : "low"}">${risk ? "⚠️ Nguy cơ cao" : "✅ An toàn"}</span></td>
      <td><strong>${(Number(h.confidence || 0) * 100).toFixed(1)}%</strong></td>
      <td>
        <button type="button" class="btn btn-sm btn-ghost delete-hist-item" data-idx="${idx}" title="Xóa dòng này">✕</button>
      </td>
    `;
    body.appendChild(tr);
  }

  // Gắn sự kiện xóa từng dòng
  body.querySelectorAll(".delete-hist-item").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const i = Number(e.currentTarget.dataset.idx);
      state.history.splice(i, 1);
      localStorage.setItem(HISTORY_KEY, JSON.stringify(state.history));
      renderHistory(filterText);
      showToast("Đã xóa 1 bản ghi lịch sử.", "info");
    });
  });
}

function exportHistoryToCSV() {
  if (state.history.length === 0) {
    showToast("Chưa có dữ liệu lịch sử để xuất file.", "warning");
    return;
  }

  const headers = ["Thoi_gian", "Ngay", "Hoc_phan", "Nhom_tuoi", "Tin_chi", "Luot_click", "Ket_qua", "Xac_suat"];
  const rows = state.history.map((h) => [
    `"${h.time}"`,
    `"${h.date || ""}"`,
    `"${h.module}"`,
    `"${h.age}"`,
    h.credits,
    h.clicks,
    h.prediction === 1 ? '"Nguy co cao"' : '"An toan"',
    (Number(h.confidence || 0) * 100).toFixed(1) + "%",
  ]);

  const csvContent = "\uFEFF" + [headers.join(","), ...rows.map((r) => r.join(","))].join("\r\n");
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `edurisk_history_${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
  showToast("Đã xuất file CSV thành công!", "success");
}

/* ---------- 11. Hệ Thống Authentication (Đăng Nhập & Đăng Ký) ---------- */
function initAuth() {
  renderAuthUI();

  // Mở modal khi bấm nút Đăng nhập
  document.addEventListener("click", (e) => {
    if (e.target.closest("#open-auth-btn")) {
      openAuthModal();
    }
  });

  // Đóng modal
  $("#close-auth-modal")?.addEventListener("click", closeAuthModal);
  $("#auth-modal")?.addEventListener("click", (e) => {
    if (e.target === $("#auth-modal")) closeAuthModal();
  });

  // Chuyển tab Đăng nhập / Đăng ký
  $("#tab-login-btn")?.addEventListener("click", () => switchAuthTab("login"));
  $("#tab-register-btn")?.addEventListener("click", () => switchAuthTab("register"));

  // Nút Demo Accounts 1-Click
  $("#demo-advisor-btn")?.addEventListener("click", () => {
    loginUser({
      name: "TS. Nguyễn Văn Minh",
      email: "advisor@university.edu.vn",
      role: "Cố vấn học tập",
    });
  });

  $("#demo-admin-btn")?.addEventListener("click", () => {
    loginUser({
      name: "ThS. Trần Thị Mai",
      email: "admin@edurisk.ai",
      role: "Quản trị viên",
    });
  });

  // Submit Form Đăng nhập
  $("#login-form")?.addEventListener("submit", (e) => {
    e.preventDefault();
    const email = $("#login-email").value.trim();
    if (!email) return;

    loginUser({
      name: email.split("@")[0].toUpperCase(),
      email: email,
      role: "Cố vấn học tập",
    });
  });

  // Submit Form Đăng ký
  $("#register-form")?.addEventListener("submit", (e) => {
    e.preventDefault();
    const name = $("#reg-name").value.trim();
    const email = $("#reg-email").value.trim();
    const roleEl = $("#reg-role");
    const roleText = roleEl.options[roleEl.selectedIndex].text;

    if (!name || !email) return;

    loginUser({
      name: name,
      email: email,
      role: roleText,
    });
  });
}

function openAuthModal() {
  $("#auth-modal")?.classList.remove("hidden");
}

function closeAuthModal() {
  $("#auth-modal")?.classList.add("hidden");
}

function switchAuthTab(tab) {
  const isLogin = tab === "login";
  $("#tab-login-btn")?.classList.toggle("active", isLogin);
  $("#tab-register-btn")?.classList.toggle("active", !isLogin);
  $("#login-form")?.classList.toggle("hidden", !isLogin);
  $("#register-form")?.classList.toggle("hidden", isLogin);
}

function loginUser(userData) {
  state.user = userData;
  localStorage.setItem(USER_KEY, JSON.stringify(userData));
  renderAuthUI();
  closeAuthModal();
  showToast(`Xin chào, ${userData.name}! Đã đăng nhập với vai trò ${userData.role}.`, "success");
}

function logoutUser() {
  state.user = null;
  localStorage.removeItem(USER_KEY);
  renderAuthUI();
  showToast("Bạn đã đăng xuất an toàn khỏi hệ thống.", "info");
}

function renderAuthUI() {
  const slot = $("#auth-nav-slot");
  if (!slot) return;

  if (state.user) {
    const initials = state.user.name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase();
    slot.innerHTML = `
      <div class="user-menu-btn" title="Vai trò: ${state.user.role} (${state.user.email})">
        <div class="user-avatar">${initials}</div>
        <span class="user-name-label">${state.user.name}</span>
        <button type="button" class="btn-logout-icon" id="logout-btn" title="Đăng xuất">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/></svg>
        </button>
      </div>
    `;
    slot.querySelector("#logout-btn")?.addEventListener("click", logoutUser);
  } else {
    slot.innerHTML = `
      <button type="button" class="btn btn-outline-primary btn-sm" id="open-auth-btn">
        <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" x2="3" y1="12" y2="12"/></svg>
        <span>Đăng nhập</span>
      </button>
    `;
  }
}

/* ---------- 12. Modal Cấu Hình Backend API ---------- */
function initBackendConfigModal() {
  const modal = $("#backend-modal");
  const input = $("#backend-url-input");

  $("#backend-status-btn")?.addEventListener("click", () => {
    if (input) input.value = state.apiBase;
    modal?.classList.remove("hidden");
    checkHealth();
  });

  $("#close-backend-modal")?.addEventListener("click", () => modal?.classList.add("hidden"));
  modal?.addEventListener("click", (e) => {
    if (e.target === modal) modal.classList.add("hidden");
  });

  $("#ping-backend-btn")?.addEventListener("click", async () => {
    await checkHealth();
    showToast("Đã kiểm tra lại kết nối máy chủ.", "info");
  });

  $("#save-backend-btn")?.addEventListener("click", () => {
    const val = normalizeBase(input.value);
    if (!val) return;
    state.apiBase = val;
    localStorage.setItem(API_BASE_KEY, val);
    modal?.classList.add("hidden");
    checkHealth();
    showToast(`Đã lưu cấu hình API mới: ${val}`, "success");
  });
}

/* ---------- 13. Gắn Sự Kiện Toàn Cục ---------- */
function bindEvents() {
  // Mẫu nhanh (Presets)
  $$("[data-preset]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const name = btn.dataset.preset;
      fillForm(name === "reset" ? null : PRESETS[name]);
      showToast(name === "reset" ? "Đã đặt lại dữ liệu form mặc định." : `Đã tải mẫu: ${btn.textContent.trim()}`, "info");
    });
  });

  // Submit Form Dự Đoán
  $("#predict-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();

    const btn = $("#submit-btn");
    const spinner = $("#submit-spinner");
    const text = $("#submit-text");

    btn.disabled = true;
    spinner?.classList.remove("hidden");
    if (text) text.textContent = "Mô hình đang phân tích…";

    let features;
    let data;

    try {
      features = collectFeatures();
      data = await predict(features);
    } catch (err) {
      console.error("Lỗi gửi dự đoán:", err);
      let msg = err.message;
      if (err.name === "TimeoutError" || err.name === "AbortError") {
        msg = "Hết thời gian chờ backend phản hồi (Timeout). Hãy kiểm tra xem uvicorn đang chạy chưa.";
      } else if (err instanceof TypeError) {
        msg = `Không kết nối được backend tại "${state.apiBase}". Hãy đảm bảo server uvicorn đang hoạt động.`;
      }
      showToast(msg, "error", 5000);
      return;
    } finally {
      btn.disabled = false;
      spinner?.classList.add("hidden");
      if (text) text.textContent = "🔍 Phân tích nguy cơ học tập";
    }

    try {
      showResult(data, features);
      addHistory(data, features);
      showToast("Phân tích hoàn tất! Đã cập nhật kết quả và khuyến nghị.", "success");
    } catch (renderErr) {
      console.error("Lỗi hiển thị kết quả:", renderErr);
      showToast(`Lỗi hiển thị giao diện: ${renderErr.message}`, "error");
    }
  });

  // Lọc lịch sử theo text input
  $("#history-filter-input")?.addEventListener("input", (e) => {
    renderHistory(e.target.value);
  });

  // Nút Xuất CSV Lịch sử
  $("#export-history-btn")?.addEventListener("click", exportHistoryToCSV);

  // Xóa toàn bộ lịch sử
  $("#clear-history")?.addEventListener("click", () => {
    if (state.history.length === 0) return;
    if (confirm("Bạn có chắc chắn muốn xóa toàn bộ lịch sử dự đoán trong phiên này?")) {
      state.history = [];
      localStorage.removeItem(HISTORY_KEY);
      renderHistory();
      showToast("Đã xóa sạch lịch sử dự đoán.", "info");
    }
  });

  // Copy khuyến nghị can thiệp
  $("#copy-rec-btn")?.addEventListener("click", () => {
    const list = $("#recommend-list");
    if (!list) return;
    const items = Array.from(list.querySelectorAll("li")).map((li, i) => `${i + 1}. ${li.textContent}`);
    if (items.length === 0) return;

    const copyText = `[EduRisk AI — Đề xuất can thiệp học tập]:\n` + items.join("\n");
    navigator.clipboard.writeText(copyText).then(() => {
      showToast("Đã sao chép các đề xuất vào clipboard!", "success");
    }).catch(() => {
      showToast("Không thể sao chép tự động, vui lòng chọn và bôi đen.", "warning");
    });
  });

  // Form Liên hệ
  $("#contact-form")?.addEventListener("submit", (e) => {
    e.preventDefault();
    const name = $("#contact-name").value.trim();
    showToast(`Cảm ơn bạn ${name}! Tin nhắn của bạn đã được gửi tới nhóm kỹ thuật.`, "success");
    $("#contact-form").reset();
  });
}

/* ---------- 14. Khởi động Ứng dụng ---------- */
document.addEventListener("DOMContentLoaded", () => {
  renderForm();
  renderHistory();
  initRouter();
  initAuth();
  initBackendConfigModal();
  bindEvents();
  startHealthPolling();
});
