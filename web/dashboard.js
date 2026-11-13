"use strict";
(() => {
  const strings = {
    zh: {
      skip: "跳到仓库目录",
      workspace: "探索数据",
      catalog: "策略仓库",
      vendors: "厂商目录",
      apk: "赏金 APK 清单",
      resources: "项目资源",
      guide: "使用文档",
      publicData: "公开数据，可追溯来源",
      sideNote: "安全策略原文与结构化索引，为你的研究提供起点。",
      viewStats: "查看统计快照 ↗",
      overview: "总览",
      headline: "从开源项目，<br><span>找到安全上报入口。</span>",
      intro:
        "聚合国内外厂商的 SECURITY.md 安全策略。<br>搜索仓库、阅读原文，让每一次研究都有据可循。",
      explore: "探索策略仓库",
      download: "下载全量 CSV",
      repoMetric: "安全策略仓库",
      repoHint: "收录 SECURITY.md 的开源项目",
      vendorMetric: "收录厂商",
      vendorHint: "科技公司、社区与开源基金会",
      orgMetric: "GitHub 组织",
      snapshot: "快照更新时间",
      swept: "{n} 个组织已完成列表采集",
      time: "{time} · 采集模式：{mode}",
      scopeNote:
        "收录安全策略不代表仓库在赏金范围内。研究前，请以厂商当前的官方范围与规则为准。",
      json: "获取 JSON 数据 ↗",
      search: "搜索仓库、厂商、语言或描述…",
      vendorLabel: "厂商",
      languageLabel: "语言",
      reset: "重置筛选",
      allVendors: "全部厂商",
      allLanguages: "全部语言",
      allSources: "全部 SRC",
      loading: "正在加载公开数据…",
      pageSize: "每页",
      repoColumn: "仓库 / 安全策略",
      stars: "星数",
      policy: "策略原文",
      local: "本地原文 ↗",
      upstream: "GitHub ↗",
      unknown: "未标注",
      result: "找到 {n} 个仓库",
      range: "显示 {from}–{to} 条，共 {total} 条",
      page: "第 {page} / {pages} 页",
      first: "首页",
      last: "末页",
      prev: "上一页",
      next: "下一页",
      empty: "没有匹配的仓库，试试其他关键词或重置筛选。",
      errorTitle: "暂时无法加载数据",
      errorBody: "请通过 HTTP 服务打开看板，或稍后重试。你也可以直接下载 CSV。",
      retry: "重新加载",
      failed: "以下组织的列表采集待重试：{orgs}",
      expand: "展开 / 收起目录",
      vendorIntro: "按收录数排列。可筛选仓库或查看厂商数据。",
      list: "仓库清单 ↗",
      footer: "公开策略索引 · 原文版权归各仓库所有者",
      contribute: "参与维护 ↗",
    },
    en: {
      skip: "Skip to repositories",
      workspace: "EXPLORE",
      catalog: "Policy repositories",
      vendors: "Vendor directory",
      apk: "Bounty APK directory",
      resources: "RESOURCES",
      guide: "Documentation",
      publicData: "Public, traceable data",
      sideNote:
        "Original security policies and structured data. A starting point for your research.",
      viewStats: "View statistics ↗",
      overview: "Overview",
      headline: "Open-source projects.<br><span>Clear reporting paths.</span>",
      intro:
        "Explore SECURITY.md policies from companies and communities.<br>Find a repository. Read the policy. Start with the source.",
      explore: "Explore policies",
      download: "Download full CSV",
      repoMetric: "Policy repositories",
      repoHint: "Open-source projects with SECURITY.md",
      vendorMetric: "Vendors indexed",
      vendorHint: "Companies, communities & foundations",
      orgMetric: "GitHub organizations",
      snapshot: "Snapshot updated",
      swept: "{n} organization lists collected",
      time: "{time} · Collection mode: {mode}",
      scopeNote:
        "A security policy does not imply bounty eligibility. Check the current official scope and rules before researching.",
      json: "Get JSON data ↗",
      search: "Search repositories, vendors, languages or descriptions…",
      vendorLabel: "Vendor",
      languageLabel: "Language",
      reset: "Reset filters",
      allVendors: "All vendors",
      allLanguages: "All languages",
      allSources: "All SRCs",
      loading: "Loading public data…",
      pageSize: "Per page",
      repoColumn: "Repository / security policy",
      stars: "Stars",
      policy: "Policy source",
      local: "Local copy ↗",
      upstream: "GitHub ↗",
      unknown: "Not specified",
      result: "{n} repositories found",
      range: "Showing {from}–{to} of {total}",
      page: "Page {page} / {pages}",
      first: "First",
      last: "Last",
      prev: "Previous",
      next: "Next",
      empty:
        "No matching repositories. Try another keyword or reset the filters.",
      errorTitle: "Unable to load data",
      errorBody:
        "Open this dashboard through an HTTP server, or try again later. You can also download the CSV directly.",
      retry: "Try again",
      failed: "Organization lists pending retry: {orgs}",
      expand: "Expand / collapse directory",
      vendorIntro:
        "Sorted by repository count. Filter the collection or view vendor data.",
      list: "Repository list ↗",
      footer:
        "Public policy index · Policy copyrights belong to their respective owners",
      contribute: "Contribute ↗",
    },
  };
  const $ = (id) => document.getElementById(id);
  const validSort = ["f", "v", "l", "s"];
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
  const nrm = (value) => String(value ?? "").toLocaleLowerCase();
  const storedLanguage = () => {
    try {
      return localStorage.getItem("secmd_lang");
    } catch {
      return null;
    }
  };
  let lang = "zh",
    state,
    repos = [],
    stats = null,
    filtered = [],
    ready = false;
  function readState() {
    const p = new URLSearchParams(location.search);
    const language = p.get("lang") || storedLanguage();
    lang = ["zh", "en"].includes(language) ? language : "zh";
    state = {
      q: p.get("q") || "",
      v: p.get("vendor") || "",
      l: p.get("language") || "",
      src: p.get("src") || "",
      sort: validSort.includes(p.get("sort")) ? p.get("sort") : "s",
      direction: p.get("direction") === "asc" ? 1 : -1,
      page: Math.max(1, Math.floor(Number(p.get("page")) || 1)),
      size: [25, 50, 100].includes(Number(p.get("size")))
        ? Number(p.get("size"))
        : 25,
    };
  }
  const t = (key, params = {}) =>
    Object.entries(params).reduce(
      (s, [k, v]) => s.replaceAll(`{${k}}`, v),
      strings[lang][key] || key,
    );
  const number = (n) =>
    Number(n).toLocaleString(lang === "zh" ? "zh-CN" : "en-US");
  const repoURL = (r) =>
    `https://github.com/${r.f.split("/").map(encodeURIComponent).join("/")}`;
  function saveURL() {
    const p = new URLSearchParams();
    [
      ["q", state.q],
      ["vendor", state.v],
      ["language", state.l],
      ["src", state.src],
      ["sort", state.sort !== "s" ? state.sort : ""],
      ["direction", state.direction === 1 ? "asc" : ""],
      ["page", state.page > 1 ? state.page : ""],
      ["size", state.size !== 25 ? state.size : ""],
      ["lang", lang === "en" ? lang : ""],
    ].forEach(([k, v]) => {
      if (v) p.set(k, v);
    });
    try {
      history.replaceState(
        null,
        "",
        `${location.pathname}${p.size ? "?" + p.toString() : ""}${location.hash}`,
      );
    } catch {
      /* A static file preview may disallow history. */
    }
  }
  function fill(id, key, label) {
    const select = $(id);
    const values = [...new Set(repos.map((r) => r[key]).filter(Boolean))].sort(
      (a, b) => a.localeCompare(b, lang === "zh" ? "zh-CN" : "en"),
    );
    select.replaceChildren(
      new Option(t(label), ""),
      ...values.map((value) => new Option(value, value)),
    );
    if (state[key] && !values.includes(state[key]))
      select.add(new Option(state[key], state[key]));
    select.value = state[key];
  }
  function syncControls() {
    $("q").value = state.q;
    $("page-size").value = state.size;
    fill("fv", "v", "allVendors");
    fill("fl", "l", "allLanguages");
    fill("fs", "src", "allSources");
  }
  function translate() {
    document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
    document.title =
      lang === "zh"
        ? "SECURITY.md Collect · 开源安全策略索引"
        : "SECURITY.md Collect · Open-source security policies";
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      if (["headline", "intro"].includes(el.dataset.i18n))
        el.innerHTML = t(el.dataset.i18n);
      else el.textContent = t(el.dataset.i18n);
    });
    $("q").placeholder = t("search");
    $("q").setAttribute("aria-label", t("search"));
    $("langbtn").textContent = lang === "zh" ? "EN / 中文" : "中文 / EN";
    $("langbtn").setAttribute(
      "aria-label",
      lang === "zh" ? "Switch to English" : "切换到中文",
    );
    syncControls();
    renderMetrics();
    renderVendors();
    render();
  }
  function renderMetrics() {
    if (!stats) return;
    $("metric-repos").textContent = number(repos.length);
    $("nav-count").textContent = number(repos.length);
    $("metric-vendors").textContent = number(stats.totals.vendors);
    $("metric-orgs").textContent = number(stats.totals.orgs);
    $("metric-swept").textContent = t("swept", {
      n: number(stats.totals.orgs_swept),
    });
    const [date, time = ""] = String(stats.generated_at).split(" ");
    $("metric-date").textContent = date;
    $("metric-time").textContent = t("time", { time, mode: stats.mode || "—" });
    const failed = stats.orgs_failed || [];
    $("retry-note").hidden = !failed.length;
    $("retry-note").textContent = t("failed", { orgs: failed.join(", ") });
  }
  function renderVendors() {
    if (!stats) return;
    const fragment = document.createDocumentFragment();
    [...stats.vendors]
      .sort(
        (a, b) => b.sec_repos - a.sec_repos || a.vendor.localeCompare(b.vendor),
      )
      .forEach((v) => {
        const article = document.createElement("article");
        article.className = "vendor-card";
        const button = document.createElement("button");
        button.type = "button";
        const name = document.createElement("span");
        name.textContent = v.vendor;
        const count = document.createElement("b");
        count.textContent = number(v.sec_repos);
        button.append(name, count);
        button.addEventListener("click", () => {
          state.v = v.vendor;
          state.page = 1;
          $("fv").value = state.v;
          render();
          $("catalog").scrollIntoView();
        });
        const source = document.createElement("p");
        source.textContent = v.src || t("unknown");
        article.append(button, source);
        const folder = encodeURIComponent(
          v.vendor
            .replace(/[\\/:*?"<>|\r\n\t]/g, "_")
            .trim()
            .replace(/^\.+|\.+$/g, "") || "_unnamed",
        );
        [
          [t("list"), `./厂商/${folder}/清单.md`],
          ["JSON ↗", `./厂商/${folder}/repos.json`],
        ].forEach(([label, href]) => {
          const a = document.createElement("a");
          a.textContent = label;
          a.href = href;
          article.append(a);
        });
        fragment.append(article);
      });
    $("vendor-grid").replaceChildren(fragment);
  }
  const languageColors = {
    Python: "#92b6e6",
    JavaScript: "#e3d28b",
    TypeScript: "#7db3c9",
    Go: "#8cced6",
    Rust: "#d7ad93",
    "C++": "#d798b5",
    C: "#b6bac5",
    Java: "#d3af79",
    "C#": "#b1a4db",
    Ruby: "#d58b87",
    Shell: "#b2d19c",
  };
  function render() {
    if (!ready) return;
    const q = nrm(state.q.trim());
    filtered = repos.filter(
      (r) =>
        (!state.v || r.v === state.v) &&
        (!state.l || r.l === state.l) &&
        (!state.src || r.src === state.src) &&
        (!q || r.search.includes(q)),
    );
    filtered.sort((a, b) => {
      const diff =
        state.sort === "s"
          ? (a.s ?? -1) - (b.s ?? -1)
          : String(a[state.sort] || "").localeCompare(
              String(b[state.sort] || ""),
              lang === "zh" ? "zh-CN" : "en",
              { sensitivity: "base" },
            );
      return diff * state.direction || a.f.localeCompare(b.f);
    });
    const pages = Math.max(1, Math.ceil(filtered.length / state.size));
    state.page = Math.min(state.page, pages);
    const start = (state.page - 1) * state.size;
    const rows = filtered.slice(start, start + state.size);
    $("results").innerHTML =
      rows
        .map((r) => {
          const url = repoURL(r);
          const policy = `${url}/blob/HEAD/${r.path.split("/").map(encodeURIComponent).join("/")}`;
          return `<tr><td><a class="repo-title" href="${url}">${esc(r.f)}<span class="arrow" aria-hidden="true">↗</span></a>${r.lic ? `<span class="license">${esc(r.lic)}</span>` : ""}<div class="repo-description">${esc(r.d || "—")}</div></td><td><div class="vendor-name">${esc(r.v)}</div><div class="src-name">${esc(r.src || t("unknown"))}</div></td><td><span class="language" style="--lang-color:${languageColors[r.l] || "#9cb8a4"}">${esc(r.l || "—")}</span></td><td class="stars"><span class="star-icon" aria-hidden="true">☆</span>${r.s == null ? "—" : number(r.s)}</td><td><div class="policy-links">${r.loc ? `<a href="./${esc(r.loc)}" aria-label="${esc(r.f)} ${esc(t("local"))}">${t("local")}</a>` : ""}<a class="upstream" href="${policy}" aria-label="${esc(r.f)} GitHub SECURITY.md">${t("upstream")}</a></div></td></tr>`;
        })
        .join("") ||
      `<tr><td class="empty" colspan="5">${esc(t("empty"))}</td></tr>`;
    $("result-count").textContent = t("result", { n: number(filtered.length) });
    $("page-info").textContent = t("range", {
      from: filtered.length ? number(start + 1) : "0",
      to: number(Math.min(start + state.size, filtered.length)),
      total: number(filtered.length),
    });
    $("page-number").textContent = t("page", { page: state.page, pages });
    $("first").disabled = $("prev").disabled = state.page <= 1;
    $("last").disabled = $("next").disabled = state.page >= pages;
    document.querySelectorAll("th[data-sort]").forEach((th) => {
      th.setAttribute(
        "aria-sort",
        th.dataset.sort === state.sort
          ? state.direction === 1
            ? "ascending"
            : "descending"
          : "none",
      );
    });
    saveURL();
  }
  async function load() {
    ready = false;
    $("error").hidden = true;
    $("result-count").textContent = t("loading");
    try {
      const response = await fetch(
        new URL("./索引/dashboard.json", document.baseURI),
      );
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await response.json();
      if (
        !Array.isArray(payload.repos) ||
        !payload.stats?.totals ||
        !Array.isArray(payload.stats.vendors)
      )
        throw new Error("Invalid dashboard snapshot");
      repos = payload.repos.map((r) => ({
        ...r,
        search: nrm([r.f, r.v, r.l, r.src, r.lic, r.d].join(" ")),
      }));
      stats = payload.stats;
      ready = true;
      translate();
    } catch (error) {
      $("error").hidden = false;
      $("result-count").textContent = t("errorTitle");
      $("results").replaceChildren();
      console.error("Dashboard data:", error);
    }
  }
  readState();
  translate();
  load();
  let searchTimer;
  $("q").addEventListener("input", (e) => {
    state.q = e.target.value;
    state.page = 1;
    clearTimeout(searchTimer);
    searchTimer = setTimeout(render, 120);
  });
  [
    ["fv", "v"],
    ["fl", "l"],
    ["fs", "src"],
  ].forEach(([id, key]) =>
    $(id).addEventListener("change", (e) => {
      state[key] = e.target.value;
      state.page = 1;
      render();
    }),
  );
  $("reset").addEventListener("click", () => {
    state = {
      ...state,
      q: "",
      v: "",
      l: "",
      src: "",
      sort: "s",
      direction: -1,
      page: 1,
    };
    syncControls();
    render();
  });
  $("page-size").addEventListener("change", (e) => {
    state.size = Number(e.target.value);
    state.page = 1;
    render();
  });
  $("langbtn").addEventListener("click", () => {
    lang = lang === "zh" ? "en" : "zh";
    try {
      localStorage.setItem("secmd_lang", lang);
    } catch {}
    translate();
  });
  document.querySelectorAll("th[data-sort]").forEach((th) =>
    th.querySelector("button").addEventListener("click", () => {
      const key = th.dataset.sort;
      state.direction =
        key === state.sort ? -state.direction : key === "s" ? -1 : 1;
      state.sort = key;
      state.page = 1;
      render();
    }),
  );
  [
    ["first", () => 1],
    ["prev", () => state.page - 1],
    ["next", () => state.page + 1],
    ["last", () => Math.max(1, Math.ceil(filtered.length / state.size))],
  ].forEach(([id, page]) =>
    $(id).addEventListener("click", () => {
      state.page = page();
      render();
    }),
  );
  $("retry").addEventListener("click", load);
  window.addEventListener("popstate", () => {
    readState();
    translate();
  });
  document.addEventListener("keydown", (e) => {
    if (
      e.key === "/" &&
      !e.ctrlKey &&
      !e.metaKey &&
      !e.altKey &&
      !["INPUT", "TEXTAREA", "SELECT"].includes(
        document.activeElement.tagName,
      ) &&
      !document.activeElement.isContentEditable
    ) {
      e.preventDefault();
      $("q").focus();
    }
  });
})();
