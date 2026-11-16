"use strict";
(() => {
  const $ = (id) => document.getElementById(id);
  if (!$("app-discovery")) return;
  const labels = {
    zh: {
      title: "厂商应用发现", browse: "查看厂商应用与待核清单", data: "发现记录 JSON ↗",
      reviewLedger: "逐项核查结果 ↗", sourceLedger: "分页来源与停止原因 ↗",
      reviewFilter: "范围 / 接收状态", allStates: "全部状态", confirmedOnly: "已关联范围", pendingOnly: "范围待核", pausedOnly: "暂停接收也收录",
      excludedOnly: "官方明确范围排除", scopeExcluded: "官方明确范围排除",
      paused: "暂停接收 · 保留范围与应用记录", unknownSubmission: "当前接收状态待核",
      reviewSummary: "原 {total} 条候选已逐项处理：范围确认（含暂停）{confirmed} 条，错归排除 {rejected} 条，明确范围排除 {excluded} 条，仍待补证 {pending} 条。",
      intro: "逐厂商查找应用与 Android 身份。发现应用后仍需核对 SRC 范围；下方候选不计入已确认目标。",
      view: "查看", apps: "应用发现与待核", vendors: "全部厂商核查队列", reset: "重置",
      prev: "上一页", next: "下一页", placeholder: "搜索厂商、应用或包名",
      results: "{n} 条匹配 / 应用发现 {apps} 条 / 厂商队列 {vendors} 个",
      empty: "没有匹配记录。试试厂商简称，或切换到全部厂商队列。",
      error: "应用发现数据暂时无法加载，可重试或直接查看 JSON。", retry: "重试",
      scopePending: "SRC 范围待核", confirmed: "已关联 SRC 范围证据", package: "Android 包名待补",
      qimai: "七麦检索入口", source: "应用发现来源", identity: "包名核对来源", download: "应用下载页", scope: "范围证据",
      catalog: "在应用目录查找", observed: "核查时间", notChecked: "未检查",
      note: "分页账本记录实际页码、终止条件和受限队列；可见检索末页不等于厂商全部产品。应用身份、范围、奖励与接收状态分别核对，暂停接收也保留记录。",
      status: "核查状态", shell_only: "仅前端空壳", frontend_shell: "仅前端空壳",
      access_error: "接口访问受限", blocked: "访问受限", unavailable: "来源不可读",
      no_results: "本次未发现结果", pending_review: "待核查", pending: "待核查",
      checked: "已尝试检索", checked_shell: "仅前端空壳", discovered: "已发现应用",
      android_candidates_found: "已发现 Android 候选，归属与范围需核对",
      no_publisher_matched_android_in_first_search_page: "首个搜索页未发现开发者匹配的 Android 候选",
      public_api_access_error: "公开接口访问受限",
      qimaiShared: "七麦仅做共用入口探测，未逐厂商检索",
      latestSearch: "查看来源检索", paginationDone: "{source} · 已遍历 {pages} 页至所见末页", no_publisher_match_in_exhausted_search: "已遍历可见检索结果，未核实匹配应用", qimaiStatus: "七麦来源状态", candidates: "Android 候选 {n} 个",
    },
    en: {
      title: "Vendor app discovery", browse: "Browse app discoveries and gaps", data: "Discovery JSON ↗",
      reviewLedger: "Per-app review results ↗", sourceLedger: "Source pagination and stop reasons ↗",
      reviewFilter: "Scope / submission", allStates: "All states", confirmedOnly: "Scope evidence linked", pendingOnly: "Scope unresolved", pausedOnly: "Paused programs included",
      excludedOnly: "Explicitly excluded from scope", scopeExcluded: "Explicitly excluded from scope",
      paused: "Submissions paused · app and scope retained", unknownSubmission: "Current submission state unconfirmed",
      reviewSummary: "Reviewed all {total} original candidates: {confirmed} scope-confirmed (including paused), {rejected} rejected vendor matches, {excluded} explicitly excluded, {pending} still need evidence.",
      intro: "Find apps and Android identities by vendor. Discoveries still need SRC scope review and are separate from confirmed targets.",
      view: "View", apps: "Discovered apps / review queue", vendors: "All vendor checks", reset: "Reset",
      prev: "Previous", next: "Next", placeholder: "Search vendors, apps or package IDs",
      results: "{n} matches / {apps} app discoveries / {vendors} vendors",
      empty: "No matching records. Try a vendor alias or switch to all vendor checks.",
      error: "Discovery data is unavailable. Retry or open the JSON snapshot.", retry: "Retry",
      scopePending: "SRC scope needs review", confirmed: "Linked to SRC scope evidence", package: "Android package ID unavailable",
      qimai: "Search Qimai", source: "App discovery source", identity: "Package identity source", download: "App download page", scope: "Scope evidence",
      catalog: "Find in app directory", observed: "Checked", notChecked: "Not checked",
      note: "The source ledger records pages, end conditions and blocked queues. A visible search end is not a complete vendor inventory. App identity, scope, rewards and submission state remain separate; paused programs stay indexed.",
      status: "Check status", shell_only: "Frontend shell only", frontend_shell: "Frontend shell only",
      access_error: "API access restricted", blocked: "Access restricted", unavailable: "Source unavailable",
      no_results: "No results observed", pending_review: "Needs review",
      checked: "Search attempted", checked_shell: "Frontend shell only", discovered: "Apps discovered",
      android_candidates_found: "Android candidates found; ownership and scope need review",
      no_publisher_matched_android_in_first_search_page: "No publisher-matched Android candidate on the first search page",
      public_api_access_error: "Public API access restricted",
      qimaiShared: "Shared Qimai entry point probe only; vendor search not performed",
      latestSearch: "Search source", paginationDone: "{source} · {pages} pages, visible end reached", no_publisher_match_in_exhausted_search: "Visible search exhausted, no verified publisher match", qimaiStatus: "Qimai source status", candidates: "{n} Android candidates",
    },
  };
  let payload = { vendors: [], apps: [] }, ready = false, failed = false;
  let state;
  const lang = () => document.documentElement.lang.startsWith("en") ? "en" : "zh";
  const t = (key, values = {}) => Object.entries(values).reduce((s, [k, v]) => s.replaceAll(`{${k}}`, v), labels[lang()][key] || key);
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const list = (value) => Array.isArray(value) ? value : value ? [value] : [];
  const statusLabel = (value) => labels[lang()][value] || t("pending_review");
  const norm = (v) => String(v ?? "").normalize("NFKC").toLocaleLowerCase().replace(/[_/\-]+/g, " ");
  const link = (label, value) => {
    try {
      const u = new URL(value);
      return ["http:", "https:"].includes(u.protocol) && !u.username && !u.password ? `<a href="${esc(u.href)}">${esc(label)} ↗</a>` : "";
    } catch { return ""; }
  };
  function readState() {
    const p = new URLSearchParams(location.search);
    state = { q: p.get("dq") || "", view: p.get("dview") === "vendors" ? "vendors" : "apps", status: ["confirmed","pending","paused","excluded"].includes(p.get("dstatus")) ? p.get("dstatus") : "", page: Math.max(1, Math.floor(Number(p.get("dpage")) || 1)) };
  }
  function save() {
    const u = new URL(location.href);
    [["dq", state.q], ["dview", state.view === "vendors" ? "vendors" : ""], ["dstatus", state.status], ["dpage", state.page > 1 ? state.page : ""]].forEach(([k, v]) => v ? u.searchParams.set(k, v) : u.searchParams.delete(k));
    try { history.replaceState(null, "", u.pathname + u.search + u.hash); } catch { /* File previews may deny history updates. */ }
  }
  function render() {
    document.querySelectorAll("[data-discovery-i18n]").forEach((e) => e.textContent = t(e.dataset.discoveryI18n));
    $("discovery-q").placeholder = t("placeholder");
    $("discovery-q").setAttribute("aria-label", t("placeholder"));
    $("discovery-view").setAttribute("aria-label", t("view"));
    $("discovery-q").value = state.q;
    $("discovery-view").value = state.view;
    $("discovery-status").value = state.status;
    $("discovery-status").disabled = state.view === "vendors";
    $("discovery-status").setAttribute("aria-label", t("reviewFilter"));
    $("discovery-source-note").textContent = t("note");
    if (!ready) {
      $("discovery-count").textContent = failed ? t("error") : "…";
      $("discovery-results").innerHTML = failed ? `<button type="button" id="discovery-retry">${esc(t("retry"))}</button>` : "";
      $("discovery-prev").disabled = $("discovery-next").disabled = true;
      $("discovery-range").textContent = "";
      $("discovery-page").textContent = "";
      return;
    }
    const terms = norm(state.q).trim().split(/\s+/).filter(Boolean);
    const source = payload[state.view];
    const isPaused = (r) => [r.program_state,r.submission_state].some((s) => ["paused","closed","disabled"].includes(s));
    const isConfirmed = (r) => ["confirmed","in_scope","source_listed"].includes(r.scope_status) && !!link("scope",r.official_scope_source || r.scope_source || r.scope_review_source);
    const filtered = source.filter((r) => (state.view === "vendors" || !state.status || (state.status === "paused" ? isPaused(r) : state.status === "confirmed" ? isConfirmed(r) : state.status === "excluded" ? r.scope_status === "out_of_scope" : !isConfirmed(r) && r.scope_status !== "out_of_scope")) && terms.every((q) => norm([r.vendor, r.name, r.app_name, r.package, ...list(r.orgs), ...list(r.aliases), ...list(r.vendor_aliases), r.src].join(" ")).includes(q)));
    const baseline = payload.baseline_review_summary;
    const counts = baseline?.result_counts || {};
    const positive = (counts.confirmed_scope || 0) + (counts.confirmed_paused || 0);
    const rejected = (counts.ownership_mismatch || 0) + (counts.vendor_name_collision || 0) + (counts.confirmed_wrong_vendor || 0);
    const excluded = (counts.officially_excluded || 0) + (counts.out_of_scope || 0) + (counts.confirmed_out_of_scope || 0);
    $("discovery-review-summary").textContent = baseline ? t("reviewSummary", {total:baseline.baseline_candidates, confirmed:positive, rejected, excluded, pending:baseline.baseline_candidates-positive-rejected-excluded}) : "";
    const pages = Math.max(1, Math.ceil(filtered.length / 20));
    state.page = Math.min(state.page, pages);
    const start = (state.page - 1) * 20;
    $("discovery-count").textContent = t("results", { n: filtered.length, apps: payload.apps.length, vendors: payload.vendors.length });
    $("discovery-results").innerHTML = filtered.slice(start, start + 20).map((r) => {
      const vendor = r.vendor || "";
      if (state.view === "vendors") {
        const status = r.status || "notChecked";
        const qimaiStatus = !r.pagination_status && r.qimai_status ? `${t("qimaiStatus")} · ${statusLabel(r.qimai_status)}` : "";
        const qimaiCheck = !r.pagination_status && r.qimai_checked_individually === false ? t("qimaiShared") : "";
        const count = Number.isFinite(Number(r.candidate_count)) ? t("candidates", { n: Number(r.candidate_count) }) : "";
        return `<article class="app-discovery-card"><h3>${esc(vendor)}</h3><p class="apk-meta">${esc(t("status"))} · ${esc(statusLabel(status))}</p><p class="apk-meta">${esc(list(r.orgs).join(" · "))}</p>${count ? `<p class="apk-meta">${esc(count)}</p>` : ""}${r.pagination_status === "exhausted" ? `<p class="apk-meta">${esc(t("paginationDone", {source:r.pagination_source, pages:r.pagination_pages}))}</p>` : ""}${qimaiStatus ? `<p class="apk-meta">${esc(qimaiStatus)}</p>` : ""}${qimaiCheck ? `<p class="apk-meta">${esc(qimaiCheck)}</p>` : ""}<p class="apk-meta">${esc(r.notes || "")}</p><div class="apk-links">${link(t("latestSearch"), r.search_url)}${!r.pagination_status ? link(t("qimai"), r.qimai_url) : ""}${link(t("catalog"), new URL(`?bounty=all&q=${encodeURIComponent(vendor)}#apk-catalog`, location.href).href)}</div><p class="apk-meta">${esc(t("observed"))} · ${esc(r.checked_at || t("notChecked"))}</p></article>`;
      }
      const scopeSource = r.official_scope_source || r.scope_source || r.scope_review_source;
      const scopeLink = link(t("scope"), scopeSource);
      const confirmed = ["confirmed", "in_scope", "source_listed"].includes(r.scope_status) && !!scopeLink;
      const identitySource = r.package_source_url;
      const discoverySource = r.discovery_source_url || r.source_url;
      const discoveryLink = discoverySource !== identitySource ? link(t("source"), discoverySource) : "";
      const submission = isPaused(r) ? t("paused") : r.submission_state === "unknown" ? t("unknownSubmission") : "";
      return `<article class="app-discovery-card"><h3>${esc(r.name || r.app_name || r.package || vendor)}</h3><p class="apk-meta">${esc(vendor)} · ${esc(confirmed ? t("confirmed") : r.scope_status === "out_of_scope" ? t("scopeExcluded") : t("scopePending"))}</p>${submission ? `<p class="apk-review">${esc(submission)}</p>` : ""}<code class="package">${esc(r.package || t("package"))}</code><p class="apk-meta">${esc(r.notes || "")}</p><div class="apk-links">${link(t("identity"), identitySource)}${discoveryLink}${link(t("qimai"), r.qimai_url)}${link(t("download"), r.download_page)}${scopeLink}${link(t("catalog"), new URL(`?platform=${r.catalog_platform === "official" ? "official" : "src"}&bounty=all&q=${encodeURIComponent(r.package || r.name || vendor)}#apk-catalog`, location.href).href)}</div></article>`;
    }).join("") || `<p class="empty">${esc(t("empty"))}</p>`;
    $("discovery-range").textContent = `${filtered.length ? start + 1 : 0}–${Math.min(start + 20, filtered.length)} / ${filtered.length}`;
    $("discovery-page").textContent = `${state.page} / ${pages}`;
    $("discovery-prev").disabled = state.page <= 1;
    $("discovery-next").disabled = state.page >= pages;
    save();
  }
  async function load() {
    failed = false;
    render();
    try {
      const response = await fetch(new URL("./vendor-app-discovery.json", document.baseURI));
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      if (!Array.isArray(data.vendors) || !Array.isArray(data.apps)) throw new Error("Invalid discovery snapshot");
      payload = {
        ...data,
        vendors: data.vendors.filter((row) => row && typeof row === "object" && !Array.isArray(row)),
        apps: data.apps.filter((row) => row && typeof row === "object" && !Array.isArray(row)),
      };
      ready = true;
    } catch { failed = true; }
    render();
  }
  readState();
  $("discovery-q").addEventListener("input", (e) => { state.q = e.target.value; state.page = 1; render(); });
  $("discovery-view").addEventListener("change", (e) => { state.view = e.target.value; state.page = 1; render(); });
  $("discovery-status").addEventListener("change", (e) => { state.status = e.target.value; state.page = 1; render(); });
  $("discovery-reset").addEventListener("click", () => { state = { q: "", view: "apps", status: "", page: 1 }; render(); });
  $("discovery-prev").addEventListener("click", () => { state.page -= 1; render(); });
  $("discovery-next").addEventListener("click", () => { state.page += 1; render(); });
  $("discovery-results").addEventListener("click", (e) => { if (e.target.closest("#discovery-retry")) load(); });
  window.addEventListener("popstate", () => { readState(); render(); });
  new MutationObserver(render).observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] });
  load();
})();
