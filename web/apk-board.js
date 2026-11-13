"use strict";
(() => {
  const I18N = {
    zh: {
      skip: "跳到应用目录",
      explore: "探索数据",
      policies: "策略仓库",
      vendors: "厂商目录",
      directory: "Android 应用目录",
      navDirectory: "赏金 APK 目录",
      playTarget: "Google Play 应用",
      androidTarget: "Android 应用",
      resources: "项目资源",
      guide: "分类说明与源数据",
      public: "公开快照，来源可追溯",
      sideNote: "从项目官方范围与应用标识出发，找到合适的获取入口。",
      home: "返回项目首页 ↗",
      appearance: "外观",
      light: "明亮",
      dark: "深色",
      system: "跟随系统",
      headline: "从公开目标，<br><span>找到 Android 应用入口。</span>",
      intro:
        "汇集四大平台的公开 Android 目标。<br>查赏金状态、找包名，直达项目、Play 与镜像候选。",
      browse: "浏览有赏金目标",
      csv: "下载全量 CSV",
      totalLabel: "公开目标条目",
      totalHint: "包含多平台与同包名重复目标",
      cashLabel: "有赏金目标",
      cashHint: "根据快照中的明确赏金字段",
      packageLabel: "有包名的目标",
      packageHint: "可查看 Play 与镜像候选入口",
      programLabel: "公开项目",
      programHint: "按平台与项目页面去重",
      scope:
        "镜像地址仅为候选，未验证可下载；赏金与范围以项目当前官方规则为准。",
      json: "获取 JSON 数据 ↗",
      platform: "平台",
      allPlatforms: "全部平台",
      reward: "赏金",
      cash: "有赏金",
      allRewards: "全部状态",
      vdp: "VDP / 无赏金",
      points: "积分",
      unknown: "待确认",
      inactive: "已归档 / 不接收",
      entry: "入口",
      allEntries: "全部入口状态",
      withEntry: "有应用入口",
      missingEntry: "仅项目页 / 待补包名",
      review: "包名待核对",
      reset: "重置筛选",
      loading: "首屏已展示前 25 条有赏金记录，正在加载完整数据…",
      perPage: "每页",
      program: "项目 / 平台 ↕",
      target: "Android 目标 / 包名",
      links: "应用入口",
      first: "首页",
      prev: "上一页",
      next: "下一页",
      last: "末页",
      notes: "数据说明",
      expand: "展开 / 收起 +",
      notesBody:
        "有包名不等于已验证应用归属；人工映射条目需先核对官方项目与 Play 页面。第三方镜像可能需要代理或已失效，XAPK 也不等于单个 APK 文件。",
      generated: "快照整理时间：",
      notLive: " · 非实时检测",
      source: "阅读源数据与分类说明 ↗",
      footer: "公开 Android 目标索引 · 以官方当前政策为准",
      contribute: "参与维护 ↗",
      search: "搜索项目、Android 目标或包名…",
      result: "找到 {n} 条 / 全部 {total} 条",
      range: "显示 {from}–{to} 条，共 {total} 条",
      page: "第 {n} / {pages} 页",
      empty: "没有匹配记录，试试其他关键词或选择“全部状态”。",
      project: "项目页",
      direct: "来源 APK",
      xapk: "XAPK 候选",
      apk: "APK 候选",
      missing: "包名待补充",
      manual: "人工映射 · 待核对",
      fromPlay: "Play 链接提取",
      unspecified: "包名来源未标注",
      platformStats: "{cash} 有赏金 / {entries} 个入口",
      errorTitle: "完整数据暂时无法加载",
      errorBody: "下方保留首屏快照，也可下载全量 CSV 或重试。",
      retry: "重新加载",
    },
    en: {
      skip: "Skip to app directory",
      explore: "EXPLORE",
      policies: "Policy repositories",
      vendors: "Vendor directory",
      directory: "Android app directory",
      navDirectory: "Bounty APKs",
      playTarget: "Google Play app",
      androidTarget: "Android app",
      resources: "RESOURCES",
      guide: "Documentation & source data",
      public: "Public, traceable snapshots",
      sideNote:
        "Start with official program scopes and app identifiers to find an acquisition path.",
      home: "Back to project home ↗",
      appearance: "Appearance",
      light: "Light",
      dark: "Dark",
      system: "System",
      headline:
        "Public Android targets.<br><span>Clear acquisition paths.</span>",
      intro:
        "Explore public Android targets from four platforms.<br>Check bounty status, package IDs, Play pages and mirror candidates.",
      browse: "Browse bounty targets",
      csv: "Download full CSV",
      totalLabel: "Public target records",
      totalHint: "May repeat apps across targets or platforms",
      cashLabel: "Bounty-eligible targets",
      cashHint: "Based on explicit snapshot fields",
      packageLabel: "Targets with package IDs",
      packageHint: "Play pages and mirror candidates available",
      programLabel: "Public programs",
      programHint: "Unique platform and program URL pairs",
      scope:
        "Mirror URLs are unverified candidates. Check the program’s current official scope and bounty rules.",
      json: "Get JSON data ↗",
      platform: "Platform",
      allPlatforms: "All platforms",
      reward: "Bounty",
      cash: "Bounty eligible",
      allRewards: "All statuses",
      vdp: "VDP / no bounty",
      points: "Points",
      unknown: "Unconfirmed",
      inactive: "Archived / not accepting",
      entry: "Access",
      allEntries: "All access states",
      withEntry: "With app links",
      missingEntry: "Program only / no package ID",
      review: "Package needs review",
      reset: "Reset filters",
      loading: "Showing the first 25 bounty records while full data loads…",
      perPage: "Per page",
      program: "Program / platform ↕",
      target: "Android target / package ID",
      links: "App links",
      first: "First",
      prev: "Previous",
      next: "Next",
      last: "Last",
      notes: "About the data",
      expand: "Expand / collapse +",
      notesBody:
        "A package ID is not proof of app ownership. Check manually mapped IDs against the official program and Play listing. Third-party mirrors may require a proxy or be unavailable; XAPK is not a single APK file.",
      generated: "Snapshot assembled: ",
      notLive: " · No live availability checks",
      source: "Read source data & documentation ↗",
      footer: "Public Android target index · Current official rules apply",
      contribute: "Contribute ↗",
      search: "Search programs, Android targets or package IDs…",
      result: "{n} matching / {total} total records",
      range: "Showing {from}–{to} of {total}",
      page: "Page {n} / {pages}",
      empty:
        "No matching records. Try another keyword or select “All statuses”.",
      project: "Program",
      direct: "Source APK",
      xapk: "XAPK candidate",
      apk: "APK candidate",
      missing: "Package ID not available",
      manual: "Manual mapping · review",
      fromPlay: "Extracted from Play URL",
      unspecified: "Package source unspecified",
      platformStats: "{cash} bounty / {entries} with links",
      errorTitle: "Full data is temporarily unavailable",
      errorBody:
        "The first-page snapshot remains available. Download the full CSV or try again.",
      retry: "Try again",
    },
  };
  const $ = (id) => document.getElementById(id);
  const names = {
    h1: "HackerOne",
    intigriti: "Intigriti",
    bugcrowd: "Bugcrowd",
    ywh: "YesWeHack",
  };
  const esc = (value) =>
    String(value ?? "").replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
  const safeURL = (value) => {
    try {
      const url = new URL(value);
      return ["https:", "http:"].includes(url.protocol) &&
        !url.username &&
        !url.password
        ? url.href
        : "";
    } catch {
      return "";
    }
  };
  let rows = [],
    stats = null,
    filtered = [],
    ready = false,
    lang = "zh";
  let state;
  const t = (key, values = {}) =>
    Object.entries(values).reduce(
      (text, [key, value]) => text.replaceAll("{" + key + "}", value),
      I18N[lang][key] || key,
    );
  const number = (value) =>
    Number(value).toLocaleString(lang === "zh" ? "zh-CN" : "en-US");
  function readState() {
    const p = new URLSearchParams(location.search);
    let stored;
    try {
      stored = localStorage.getItem("secmd_lang");
    } catch {}
    lang = (p.get("lang") || stored) === "en" ? "en" : "zh";
    const bounty = p.get("bounty") || "cash";
    state = {
      q: p.get("q") || "",
      platform: names[p.get("platform")] ? p.get("platform") : "",
      bounty: ["cash", "all", "vdp", "points", "unknown", "inactive"].includes(
        bounty,
      )
        ? bounty
        : "cash",
      access: ["with", "missing", "review"].includes(p.get("access"))
        ? p.get("access")
        : "",
      page: Math.max(1, Math.floor(Number(p.get("page")) || 1)),
      size: [25, 50, 100].includes(Number(p.get("size")))
        ? Number(p.get("size"))
        : 25,
      desc: p.get("order") === "desc",
    };
  }
  function saveURL() {
    const p = new URLSearchParams();
    [
      ["q", state.q],
      ["platform", state.platform],
      ["bounty", state.bounty !== "cash" ? state.bounty : ""],
      ["access", state.access],
      ["page", state.page > 1 ? state.page : ""],
      ["size", state.size !== 25 ? state.size : ""],
      ["order", state.desc ? "desc" : ""],
      ["lang", lang === "en" ? "en" : ""],
    ].forEach(([key, value]) => {
      if (value) p.set(key, value);
    });
    try {
      history.replaceState(
        null,
        "",
        location.pathname + (p.size ? "?" + p.toString() : "") + location.hash,
      );
    } catch {}
  }
  function syncControls() {
    $("apk-q").value = state.q;
    $("apk-platform").value = state.platform;
    $("apk-bounty").value = state.bounty;
    $("apk-access").value = state.access;
    $("apk-size").value = state.size;
  }
  function translate() {
    document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
    document.title =
      lang === "zh"
        ? "Android APK 目录 · SECURITY.md Collect"
        : "Android App Directory · SECURITY.md Collect";
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      if (["headline", "intro"].includes(el.dataset.i18n))
        el.innerHTML = t(el.dataset.i18n);
      else el.textContent = t(el.dataset.i18n);
    });
    $("apk-q").placeholder = t("search");
    $("apk-q").setAttribute("aria-label", t("search"));
    [
      ["theme-select", "appearance"],
      ["apk-platform", "platform"],
      ["apk-bounty", "reward"],
      ["apk-access", "entry"],
      ["apk-size", "perPage"],
    ].forEach(([id, key]) => $(id).setAttribute("aria-label", t(key)));
    $("theme-select").value = window.secmdTheme.preference;
    $("langbtn").textContent = lang === "zh" ? "EN / 中文" : "中文 / EN";
    $("langbtn").setAttribute(
      "aria-label",
      lang === "zh" ? "Switch to English" : "切换到中文",
    );
    syncControls();
    renderPlatforms();
    render();
  }
  function renderPlatforms() {
    if (!stats) return;
    $("platforms").innerHTML = stats.platforms
      .map(
        (p) =>
          `<button class="platform-card" type="button" data-platform="${esc(p.key)}" aria-pressed="${state.platform === p.key}"><b>${esc(p.name)}</b><strong>${number(p.targets)}</strong><span>${esc(t("platformStats", { cash: number(p.cash), entries: number(p.entries) }))}</span></button>`,
      )
      .join("");
  }
  function link(label, value, mirror = false) {
    const url = safeURL(value);
    return url
      ? `<a${mirror ? ' class="mirror"' : ""} href="${esc(url)}">${esc(label)} ↗</a>`
      : "";
  }
  function rowHTML(row) {
    const targetURL = safeURL(row.target);
    const target =
      targetURL && new URL(targetURL).hostname === "play.google.com"
        ? t("playTarget")
        : row.package && row.target === row.package
          ? t("androidTarget")
          : row.target;
    const source =
      row.package_source === "manual"
        ? "manual"
        : row.package_source === "play"
          ? "fromPlay"
          : "unspecified";
    return `<tr><td>${link(row.program, row.url)}<div class="apk-meta">${esc(names[row.platform] || row.platform)} · ${esc(t(row.bounty))}</div></td><td><div class="target-text" title="${esc(row.target)}">${esc(target)}</div><code class="package">${esc(row.package || t("missing"))}</code>${row.package ? `<span class="apk-review">${esc(t(source))}</span>` : ""}</td><td><span class="reward-badge">${esc(t(row.bounty))}</span><div class="apk-meta">${esc(row.reward)}</div></td><td><div class="apk-links">${link(t("project"), row.url)}${link("Google Play", row.play)}${link(t("direct"), row.apk_direct)}${link(t("xapk"), row.xapk, true)}${link(t("apk"), row.apk, true)}</div></td></tr>`;
  }
  function render() {
    if (!ready) return;
    const q = state.q.trim().toLowerCase();
    filtered = rows.filter(
      (r) =>
        (!state.platform || r.platform === state.platform) &&
        (state.bounty === "all" || r.bounty === state.bounty) &&
        (!q || r.search.includes(q)) &&
        (!state.access ||
          (state.access === "with"
            ? !!(r.play || r.apk_direct || r.xapk)
            : state.access === "missing"
              ? !(r.play || r.apk_direct || r.xapk)
              : r.needs_review)),
    );
    const collator = new Intl.Collator(lang === "zh" ? "zh-CN" : "en", {
      sensitivity: "base",
    });
    filtered.sort(
      (a, b) =>
        (collator.compare(a.program, b.program) ||
          collator.compare(a.package, b.package)) * (state.desc ? -1 : 1),
    );
    const pages = Math.max(1, Math.ceil(filtered.length / state.size));
    state.page = Math.min(state.page, pages);
    const start = (state.page - 1) * state.size;
    $("apk-results").innerHTML =
      filtered
        .slice(start, start + state.size)
        .map(rowHTML)
        .join("") ||
      `<tr><td class="empty" colspan="4">${esc(t("empty"))}</td></tr>`;
    $("apk-count").textContent = t("result", {
      n: number(filtered.length),
      total: number(rows.length),
    });
    $("apk-page-info").textContent = t("range", {
      from: filtered.length ? number(start + 1) : 0,
      to: number(Math.min(start + state.size, filtered.length)),
      total: number(filtered.length),
    });
    $("apk-page-number").textContent = t("page", { n: state.page, pages });
    $("apk-first").disabled = $("apk-prev").disabled = state.page <= 1;
    $("apk-next").disabled = $("apk-last").disabled = state.page >= pages;
    $("apk-sort").parentElement.setAttribute(
      "aria-sort",
      state.desc ? "descending" : "ascending",
    );
    document
      .querySelectorAll("[data-platform]")
      .forEach((button) =>
        button.setAttribute(
          "aria-pressed",
          button.dataset.platform === state.platform,
        ),
      );
    saveURL();
  }
  async function load() {
    $("apk-error").hidden = true;
    try {
      const response = await fetch(
        new URL("./dashboard.json", document.baseURI),
      );
      if (!response.ok) throw new Error("HTTP " + response.status);
      const payload = await response.json();
      if (
        !Array.isArray(payload.rows) ||
        !Array.isArray(payload.stats?.platforms)
      )
        throw new Error("Invalid APK snapshot");
      rows = payload.rows.map((r) => ({
        ...r,
        search: [r.program, r.target, r.package, r.platform, r.reward]
          .join(" ")
          .toLowerCase(),
      }));
      stats = payload.stats;
      ready = true;
      translate();
    } catch (error) {
      $("apk-error").hidden = false;
      $("apk-count").textContent = t("errorTitle");
      console.error("APK snapshot:", error);
    }
  }
  readState();
  translate();
  load();
  let timer;
  $("apk-q").addEventListener("input", (event) => {
    state.q = event.target.value;
    state.page = 1;
    clearTimeout(timer);
    timer = setTimeout(render, 120);
  });
  [
    ["apk-platform", "platform"],
    ["apk-bounty", "bounty"],
    ["apk-access", "access"],
  ].forEach(([id, key]) =>
    $(id).addEventListener("change", (event) => {
      state[key] = event.target.value;
      state.page = 1;
      render();
    }),
  );
  $("platforms").addEventListener("click", (event) => {
    const button = event.target.closest("[data-platform]");
    if (button) {
      state.platform =
        state.platform === button.dataset.platform
          ? ""
          : button.dataset.platform;
      state.page = 1;
      syncControls();
      render();
    }
  });
  $("apk-size").addEventListener("change", (event) => {
    state.size = Number(event.target.value);
    state.page = 1;
    render();
  });
  $("apk-reset").addEventListener("click", () => {
    state = {
      q: "",
      platform: "",
      bounty: "cash",
      access: "",
      page: 1,
      size: 25,
      desc: false,
    };
    syncControls();
    render();
  });
  $("apk-sort").addEventListener("click", () => {
    state.desc = !state.desc;
    state.page = 1;
    render();
  });
  [
    ["apk-first", () => 1],
    ["apk-prev", () => state.page - 1],
    ["apk-next", () => state.page + 1],
    ["apk-last", () => Math.max(1, Math.ceil(filtered.length / state.size))],
  ].forEach(([id, page]) =>
    $(id).addEventListener("click", () => {
      state.page = page();
      render();
    }),
  );
  $("langbtn").addEventListener("click", () => {
    lang = lang === "zh" ? "en" : "zh";
    try {
      localStorage.setItem("secmd_lang", lang);
    } catch {}
    translate();
  });
  $("apk-retry").addEventListener("click", load);
  window.addEventListener("popstate", () => {
    readState();
    translate();
  });
  document.addEventListener("keydown", (event) => {
    if (
      event.key === "/" &&
      !event.ctrlKey &&
      !event.metaKey &&
      !event.altKey &&
      !["INPUT", "TEXTAREA", "SELECT"].includes(
        document.activeElement.tagName,
      ) &&
      !document.activeElement.isContentEditable
    ) {
      event.preventDefault();
      $("apk-q").focus();
    }
  });
})();
