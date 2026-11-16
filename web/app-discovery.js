"use strict";
(() => {
  const $ = (id) => document.getElementById(id);
  if (!$("app-discovery")) return;
  const labels = {
    zh: {
      title: "厂商应用发现", browse: "查看厂商应用与待核清单", data: "发现记录 JSON ↗",
      intro: "逐厂商查找应用与 Android 身份。发现应用后仍需核对 SRC 范围；下方候选不计入已确认目标。",
      view: "查看", apps: "应用发现与待核", vendors: "全部厂商核查队列", reset: "重置",
      prev: "上一页", next: "下一页", placeholder: "搜索厂商、应用或包名",
      results: "{n} 条匹配 / 应用发现 {apps} 条 / 厂商队列 {vendors} 个",
      empty: "没有匹配记录。试试厂商简称，或切换到全部厂商队列。",
      error: "应用发现数据暂时无法加载，可重试或直接查看 JSON。", retry: "重试",
      scopePending: "SRC 范围待核", confirmed: "已关联 SRC 范围证据", package: "Android 包名待补",
      qimai: "七麦检索入口", source: "应用发现来源", identity: "包名核对来源", download: "应用下载页", scope: "范围证据",
      catalog: "在 SRC 目录查找", observed: "核查时间", notChecked: "未检查",
      note: "七麦检索链接是发现入口；页面空壳、访问受限和未检查均不代表该厂商没有应用。商店身份不等于 SRC 范围或奖金资格。",
      status: "核查状态", shell_only: "仅前端空壳", frontend_shell: "仅前端空壳",
      access_error: "接口访问受限", blocked: "访问受限", unavailable: "来源不可读",
      no_results: "本次未发现结果", pending_review: "待核查", pending: "待核查",
      checked: "已尝试检索", checked_shell: "仅前端空壳", discovered: "已发现应用",
      android_candidates_found: "已发现 Android 候选，归属与范围需核对",
      no_publisher_matched_android_in_first_search_page: "首个搜索页未发现开发者匹配的 Android 候选",
      public_api_access_error: "公开接口访问受限",
      qimaiShared: "七麦仅做共用入口探测，未逐厂商检索",
      qimaiStatus: "七麦来源状态", candidates: "Android 候选 {n} 个",
    },
    en: {
      title: "Vendor app discovery", browse: "Browse app discoveries and gaps", data: "Discovery JSON ↗",
      intro: "Find apps and Android identities by vendor. Discoveries still need SRC scope review and are separate from confirmed targets.",
      view: "View", apps: "Discovered apps / review queue", vendors: "All vendor checks", reset: "Reset",
      prev: "Previous", next: "Next", placeholder: "Search vendors, apps or package IDs",
      results: "{n} matches / {apps} app discoveries / {vendors} vendors",
      empty: "No matching records. Try a vendor alias or switch to all vendor checks.",
      error: "Discovery data is unavailable. Retry or open the JSON snapshot.", retry: "Retry",
      scopePending: "SRC scope needs review", confirmed: "Linked to SRC scope evidence", package: "Android package ID unavailable",
      qimai: "Search Qimai", source: "App discovery source", identity: "Package identity source", download: "App download page", scope: "Scope evidence",
      catalog: "Find in SRC directory", observed: "Checked", notChecked: "Not checked",
      note: "Qimai links are discovery entry points. A frontend shell, access error or pending check does not mean a vendor has no apps. Store identity does not establish SRC scope or bounty eligibility.",
      status: "Check status", shell_only: "Frontend shell only", frontend_shell: "Frontend shell only",
      access_error: "API access restricted", blocked: "Access restricted", unavailable: "Source unavailable",
      no_results: "No results observed", pending_review: "Needs review",
      checked: "Search attempted", checked_shell: "Frontend shell only", discovered: "Apps discovered",
      android_candidates_found: "Android candidates found; ownership and scope need review",
      no_publisher_matched_android_in_first_search_page: "No publisher-matched Android candidate on the first search page",
      public_api_access_error: "Public API access restricted",
      qimaiShared: "Shared Qimai entry point probe only; vendor search not performed",
      qimaiStatus: "Qimai source status", candidates: "{n} Android candidates",
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
    state = { q: p.get("dq") || "", view: p.get("dview") === "vendors" ? "vendors" : "apps", page: Math.max(1, Math.floor(Number(p.get("dpage")) || 1)) };
  }
  function save() {
    const u = new URL(location.href);
    [["dq", state.q], ["dview", state.view === "vendors" ? "vendors" : ""], ["dpage", state.page > 1 ? state.page : ""]].forEach(([k, v]) => v ? u.searchParams.set(k, v) : u.searchParams.delete(k));
    try { history.replaceState(null, "", u.pathname + u.search + u.hash); } catch { /* File previews may deny history updates. */ }
  }
  function render() {
    document.querySelectorAll("[data-discovery-i18n]").forEach((e) => e.textContent = t(e.dataset.discoveryI18n));
    $("discovery-q").placeholder = t("placeholder");
    $("discovery-q").setAttribute("aria-label", t("placeholder"));
    $("discovery-view").setAttribute("aria-label", t("view"));
    $("discovery-q").value = state.q;
    $("discovery-view").value = state.view;
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
    const filtered = source.filter((r) => terms.every((q) => norm([r.vendor, r.name, r.app_name, r.package, ...list(r.orgs), ...list(r.aliases), r.src].join(" ")).includes(q)));
    const pages = Math.max(1, Math.ceil(filtered.length / 20));
    state.page = Math.min(state.page, pages);
    const start = (state.page - 1) * 20;
    $("discovery-count").textContent = t("results", { n: filtered.length, apps: payload.apps.length, vendors: payload.vendors.length });
    $("discovery-results").innerHTML = filtered.slice(start, start + 20).map((r) => {
      const vendor = r.vendor || "";
      if (state.view === "vendors") {
        const status = r.status || "notChecked";
        const qimaiStatus = r.qimai_status ? `${t("qimaiStatus")} · ${statusLabel(r.qimai_status)}` : "";
        const qimaiCheck = r.qimai_checked_individually === false ? t("qimaiShared") : "";
        const count = Number.isFinite(Number(r.candidate_count)) ? t("candidates", { n: Number(r.candidate_count) }) : "";
        return `<article class="app-discovery-card"><h3>${esc(vendor)}</h3><p class="apk-meta">${esc(t("status"))} · ${esc(statusLabel(status))}</p><p class="apk-meta">${esc(list(r.orgs).join(" · "))}</p>${count ? `<p class="apk-meta">${esc(count)}</p>` : ""}${qimaiStatus ? `<p class="apk-meta">${esc(qimaiStatus)}</p>` : ""}${qimaiCheck ? `<p class="apk-meta">${esc(qimaiCheck)}</p>` : ""}<p class="apk-meta">${esc(r.notes || "")}</p><div class="apk-links">${link(t("qimai"), r.qimai_url)}${link(t("catalog"), new URL(`?platform=src&bounty=all&q=${encodeURIComponent(vendor)}#apk-catalog`, location.href).href)}</div><p class="apk-meta">${esc(t("observed"))} · ${esc(r.checked_at || t("notChecked"))}</p></article>`;
      }
      const scopeSource = r.official_scope_source || r.scope_source || r.scope_review_source;
      const scopeLink = link(t("scope"), scopeSource);
      const confirmed = ["confirmed", "in_scope", "source_listed"].includes(r.scope_status) && !!scopeLink;
      const identitySource = r.package_source_url;
      const discoverySource = r.discovery_source_url || r.source_url;
      const discoveryLink = discoverySource !== identitySource ? link(t("source"), discoverySource) : "";
      return `<article class="app-discovery-card"><h3>${esc(r.name || r.app_name || r.package || vendor)}</h3><p class="apk-meta">${esc(vendor)} · ${esc(confirmed ? t("confirmed") : t("scopePending"))}</p><code class="package">${esc(r.package || t("package"))}</code><p class="apk-meta">${esc(r.notes || "")}</p><div class="apk-links">${link(t("identity"), identitySource)}${discoveryLink}${link(t("qimai"), r.qimai_url)}${link(t("download"), r.download_page)}${scopeLink}${link(t("catalog"), new URL(`?platform=src&bounty=all&q=${encodeURIComponent(r.package || r.name || vendor)}#apk-catalog`, location.href).href)}</div></article>`;
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
  $("discovery-reset").addEventListener("click", () => { state = { q: "", view: "apps", page: 1 }; render(); });
  $("discovery-prev").addEventListener("click", () => { state.page -= 1; render(); });
  $("discovery-next").addEventListener("click", () => { state.page += 1; render(); });
  $("discovery-results").addEventListener("click", (e) => { if (e.target.closest("#discovery-retry")) load(); });
  window.addEventListener("popstate", () => { readState(); render(); });
  new MutationObserver(render).observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] });
  load();
})();
