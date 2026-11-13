# -*- coding: utf-8 -*-
"""大厂开源项目 SECURITY.MD 收集器（由每 30 分钟的定时任务调用）

模式自动选择:
  search : 有 GitHub token（env GH_TOKEN/GITHUB_TOKEN、资产/.gh_token）
           -> /search/code 按 org 一把查出全部 SECURITY.md，最快
  html   : 无 token -> 抓 github.com 仓库列表页 + raw.githubusercontent 探测 SECURITY.md
           （代理可通过 SECMD_PROXY 或 config.json 显式配置，默认校验 TLS）

断点续跑: 索引/state.json + 索引/orgs/{org}.json（仓库元数据缓存）
进程锁  : 脚本/collect.lock（2 小时内的锁视为存活，防止定时任务叠加并发）
"""
import argparse
import csv
import json
import os
import re
import subprocess
import sys
import threading
import time
import random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote

import requests

BASE = Path(os.environ.get("SECMD_BASE") or (Path(__file__).resolve().parents[1]))
SCRIPTS = BASE / "脚本"
ASSETS = BASE / "资产"
INDEX = BASE / "索引"
VDIR = BASE / "厂商"
CFG_PATH = SCRIPTS / "config.json"
STATE_PATH = INDEX / "state.json"
LOCK_PATH = SCRIPTS / "collect.lock"
META_DIR = INDEX / "orgs"

DEFAULT_CFG = {
    "proxy": "",
    "port": 8899,
    "threads_probe": 12,
    "threads_download": 12,
    "run_budget_sec": 1500,
    "org_resweep_hours": 6,
    "html_sleep_sec": 0.4,
    "page_cap_profile": 200,
    "page_cap_org": 260,
}
try:
    DEFAULT_CFG.update(json.loads(CFG_PATH.read_text(encoding="utf-8")))
except Exception:
    pass
CFG = DEFAULT_CFG
PROXY = os.environ.get("SECMD_PROXY", CFG.get("proxy", "")) or None

SEC_CANDIDATES = [
    "SECURITY.md", "security.md", "Security.md",
    ".github/SECURITY.md", ".github/security.md",
    "docs/SECURITY.md", "docs/security.md",
]

LOG_LOCK = threading.Lock()


def log(msg):
    line = "[%s] %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg)
    with LOG_LOCK:
        try:
            with open(SCRIPTS / "collect.log", "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass
        try:
            print(line, flush=True)
        except Exception:
            pass


# ---------------------------------------------------------------- HTTP 层
# 传输顺序: api 直连优先（本机实测直连稳），网页/raw 走代理优先
TRANSPORT_ORDER = {
    "api": [None, PROXY] if PROXY else [None],
    "web": [PROXY, None] if PROXY else [None],
    "raw": [PROXY, None] if PROXY else [None],
}
_TLS = threading.local()


def _session():
    if not hasattr(_TLS, "s"):
        s = requests.Session()
        s.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) sec-md-collector/1.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.8",
        })
        _TLS.s = s
    return _TLS.s


def http_get(url, cls="web", timeout=25, token=None):
    """返回 (status, body)。0 = 所有传输通道都失败。"""
    last_exc = None
    extra_headers = {"Authorization": "Bearer %s" % token} if token else None
    for pr in TRANSPORT_ORDER.get(cls, [None, PROXY]):
        proxies = None if pr is None else {"http": pr, "https": pr}
        for attempt in range(2):
            try:
                r = _session().get(url, timeout=timeout, proxies=proxies,
                                   allow_redirects=True, headers=extra_headers)
                return r.status_code, r.content
            except requests.RequestException as e:
                last_exc = e
                time.sleep(0.6 * (attempt + 1))
    log("HTTP 全通道失败: %s (%s)" % (url[:110], last_exc))
    return 0, b""


def find_token():
    for k in ("GH_TOKEN", "GITHUB_TOKEN"):
        v = os.environ.get(k)
        if v and v.strip():
            return v.strip()
    tf = ASSETS / ".gh_token"
    try:
        if tf.exists():
            t = tf.read_text(encoding="utf-8").strip()
            if t:
                return t
    except Exception:
        pass
    return None


# ---------------------------------------------------------------- 厂商映射合并
MAPPING_FILES = [
    ASSETS / "vendors-base.json",
    ASSETS / "厂商映射-国内.json",
    ASSETS / "厂商映射-国际.json",
    ASSETS / "厂商映射-H1BC扩展.json",
]


def safe_name(name):
    s = re.sub(r'[\\/:*?"<>|\r\n\t]', "_", str(name)).strip().strip(".")
    return s or "_unnamed"


def merge_vendors():
    vendors = []
    by_name = {}
    org_owner = {}
    mapping_files = MAPPING_FILES + sorted(
        f for f in ASSETS.glob("厂商映射-*.json") if f not in MAPPING_FILES)
    for f in mapping_files:
        if not f.exists():
            log("缺少映射文件(跳过): %s" % f.name)
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            log("映射文件解析失败(跳过): %s %s" % (f.name, e))
            continue
        if not isinstance(data, list):
            continue
        for v in data:
            if not isinstance(v, dict):
                continue
            name = (v.get("vendor") or "").strip()
            if not name:
                continue
            orgs = [o.strip() for o in (v.get("orgs") or []) if isinstance(o, str) and o.strip()]
            if name in by_name:
                ent = by_name[name]
                for o in orgs:
                    if o not in ent["orgs"]:
                        ent["orgs"].append(o)
                if v.get("src") and (not ent.get("src") or ent.get("src") == "无"):
                    ent["src"] = v["src"]
                continue
            ent = {
                "vendor": name,
                "src": (v.get("src") or "").strip(),
                "orgs": orgs,
                "unverified": [o for o in (v.get("unverified") or []) if isinstance(o, str)],
                "note": v.get("note") or "",
            }
            by_name[name] = ent
            vendors.append(ent)
    # org 归属唯一化（先到先得，映射文件顺序即优先级）
    for ent in vendors:
        ent["orgs"] = [o for o in ent["orgs"] if org_owner.setdefault(o, ent["vendor"]) == ent["vendor"]]
    (ASSETS / "vendors.json").write_text(
        json.dumps(vendors, ensure_ascii=False, indent=1), encoding="utf-8")
    org2vendor = {o: ent["vendor"] for ent in vendors for o in ent["orgs"]}
    return vendors, org2vendor


# ---------------------------------------------------------------- 状态与锁
def load_state():
    try:
        st = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        st.setdefault("repos_checked", {})
        st.setdefault("repos_data", {})
        st.setdefault("orgs", {})
        st.setdefault("search_swept", {})
        return st
    except Exception:
        if STATE_PATH.exists():
            try:
                os.replace(STATE_PATH, STATE_PATH.with_suffix(".corrupt"))
            except Exception:
                pass
    return {"repos_checked": {}, "repos_data": {}, "orgs": {}, "search_swept": {}}


def save_state(state):
    try:
        tmp = STATE_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, STATE_PATH)
    except Exception as e:
        log("state 保存失败: %s" % e)


def _pid_alive(pid):
    try:
        # tasklist 输出是本地编码(中文 Windows 为 GBK)，用字节比较避免解码异常
        out = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid],
                             capture_output=True, timeout=15).stdout
        return str(pid).encode() in out
    except Exception:
        return True


def acquire_lock():
    try:
        if LOCK_PATH.exists():
            data = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
            age = time.time() - float(data.get("ts", 0))
            if age < 7200 and _pid_alive(int(data.get("pid", 0))):
                return False
        LOCK_PATH.write_text(json.dumps({"pid": os.getpid(), "ts": time.time()}), encoding="utf-8")
        return True
    except Exception:
        return False


def release_lock():
    try:
        data = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
        if int(data.get("pid", 0)) == os.getpid():
            LOCK_PATH.unlink()
    except Exception:
        pass


def save_meta_cache(org, items):
    try:
        META_DIR.mkdir(parents=True, exist_ok=True)
        (META_DIR / (safe_name(org) + ".json")).write_text(
            json.dumps(items, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        log("meta 缓存保存失败 %s: %s" % (org, e))


def load_meta_cache(org):
    try:
        p = META_DIR / (safe_name(org) + ".json")
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


# ---------------------------------------------------------------- 仓库列表抓取
def parse_k(tok):
    try:
        t = tok.strip().replace(",", "").lower()
        if t.endswith("k"):
            return int(float(t[:-1]) * 1000)
        if t.endswith("m"):
            return int(float(t[:-1]) * 1000000)
        return int(float(t))
    except Exception:
        return None


def parse_profile_items(html_text, name):
    esc = re.escape(name)
    pat = re.compile(
        r'<a\b[^>]*?\bitemprop="name codeRepository"[^>]*?href="/%s/([A-Za-z0-9._-]+)"[^>]*>'
        r'|<a\b[^>]*?href="/%s/([A-Za-z0-9._-]+)"[^>]*?\bitemprop="name codeRepository"[^>]*>'
        % (esc, esc), re.I)
    matches = []
    seen = set()
    for m in pat.finditer(html_text):
        repo = m.group(1) or m.group(2)
        if not repo or repo.lower() in seen:
            continue
        seen.add(repo.lower())
        matches.append((m.start(), repo))
    items = {}
    for i, (pos, repo) in enumerate(matches):
        end = matches[i + 1][0] if i + 1 < len(matches) else len(html_text)
        chunk = html_text[pos:end]
        lang = None
        ml = re.search(r'itemprop="programmingLanguage">([^<]+)<', chunk)
        if ml:
            lang = ml.group(1).strip()
        stars = None
        ms = re.search(r'/%s/%s/stargazers"[\s\S]{0,800}?</a>' % (esc, re.escape(repo)), chunk)
        if ms:
            text = re.sub(r"<[^>]+>", " ", ms.group(0))
            mt = re.search(r"([\d][\d.,]*\s*[kKmM]?)", text)
            if mt:
                stars = parse_k(mt.group(1))
        desc = None
        md = re.search(r'itemprop="description"[\s\S]{0,120}?</p>', chunk)
        if md:
            desc = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", md.group(0))).strip()
            desc = re.sub(r'^itemprop="description"[^>]*', "", desc).strip()
        items["%s/%s" % (name, repo)] = {"stars": stars, "language": lang, "description": desc}
    return items


def _find_repo_list(o, depth=0):
    if depth > 14:
        return None
    if isinstance(o, list):
        if o and isinstance(o[0], dict):
            k0 = set(o[0].keys())
            if "name" in k0 and (k0 & {"stargazerCount", "stargazers_count", "description",
                                       "owner", "isFork", "isArchived", "primaryLanguage", "language"}):
                return o
        for v in o:
            r = _find_repo_list(v, depth + 1)
            if r is not None:
                return r
    elif isinstance(o, dict):
        for v in o.values():
            r = _find_repo_list(v, depth + 1)
            if r is not None:
                return r
    return None


def _norm_org_react(d, fallback_owner):
    if not isinstance(d, dict):
        return None
    name = d.get("name")
    if not name or "/" in str(name):
        return None
    owner = ""
    ow = d.get("owner")
    if isinstance(ow, dict):
        owner = ow.get("login") or ""
    elif isinstance(ow, str):
        owner = ow
    owner = owner or d.get("ownerLogin") or fallback_owner
    pl = d.get("primaryLanguage")
    lang = (pl.get("name") if isinstance(pl, dict) else None) or d.get("language")
    stars = d.get("starsCount", d.get("stargazerCount", d.get("stargazers_count")))
    try:
        stars = int(stars) if stars is not None else None
    except Exception:
        stars = None
    return {"full": "%s/%s" % (owner, name), "stars": stars, "language": lang,
            "description": d.get("description"), "license": d.get("license")}


def list_profile(name):
    items = {}
    for page in range(1, int(CFG["page_cap_profile"]) + 1):
        url = "https://github.com/%s?tab=repositories&page=%d" % (name, page)
        st, body = http_get(url, "web", timeout=30)
        if st != 200 or not body:
            return (None if page == 1 else items)
        new = parse_profile_items(body.decode("utf-8", "replace"), name)
        added = {k: v for k, v in new.items() if k not in items}
        if not added:
            break
        items.update(added)
        time.sleep(CFG["html_sleep_sec"] + random.random() * 0.3)
    return items


def list_org_react(name):
    items = {}
    for page in range(1, int(CFG["page_cap_org"]) + 1):
        url = "https://github.com/orgs/%s/repositories?page=%d" % (name, page)
        st, body = http_get(url, "web", timeout=30)
        if st != 200 or not body:
            return (None if page == 1 else items)
        html_text = body.decode("utf-8", "replace")
        page_items = {}
        for s in re.findall(r'<script type="application/json" data-target="react-app\.embeddedData">(.*?)</script>',
                            html_text, re.S):
            try:
                data = json.loads(s)
            except Exception:
                continue
            lst = _find_repo_list(data)
            if not lst:
                continue
            for d in lst:
                n = _norm_org_react(d, name)
                if n and n["full"] not in page_items:
                    page_items[n["full"]] = {k: n[k] for k in ("stars", "language", "description")}
        added = {k: v for k, v in page_items.items() if k not in items}
        if not added:
            break
        items.update(added)
        time.sleep(CFG["html_sleep_sec"] + random.random() * 0.3)
    return items


def list_repos_any(name):
    r2 = list_org_react(name)
    if r2:
        return r2, "org"
    r1 = list_profile(name)
    if r1:
        return r1, "profile"
    # 两个解析器都为空：区分「组织确无公开仓库」与「解析失败」
    for kind, url in (("empty-org", "https://api.github.com/orgs/%s" % name),
                      ("empty-user", "https://api.github.com/users/%s" % name)):
        st, body = http_get(url, "api", timeout=20)
        if st == 200:
            try:
                info = json.loads(body.decode("utf-8", "replace"))
                if int(info.get("public_repos", -1)) == 0:
                    return {}, kind
            except Exception:
                pass
            break  # 组织/用户存在且有仓库，但页面解析为空：按解析失败处理
        if st in (403, 429):
            return None, "skip"  # API 匿名配额限流：无法判别，本轮跳过不计失败
        if st == 404 and kind == "empty-org":
            continue  # 不是组织，再查 user
        break
    return None, None


# ---------------------------------------------------------------- SECURITY.md 探测
def probe_security(full):
    """返回 (sec_path, content)；sec_path ∈ str | None(确认没有) | "error"(网络失败，下轮重试)"""
    for path in SEC_CANDIDATES:
        st, body = http_get("https://raw.githubusercontent.com/%s/HEAD/%s" % (full, path),
                            "raw", timeout=20)
        if st == 200 and body and body.strip():
            return path, body
        if st == 0:
            for br in ("main", "master"):
                st2, body2 = http_get("https://cdn.jsdelivr.net/gh/%s@%s/%s" % (full, br, path),
                                      "raw", timeout=20)
                if st2 == 200 and body2 and body2.strip():
                    return path, body2
            return "error", None
        if st in (403, 429):
            return "error", None
    return None, None


def probe_and_record(state, org, vendor, names_meta, deadline):
    todo = [full for full in names_meta if full not in state["repos_checked"]]
    if not todo:
        return 0
    found = 0
    state_lock = threading.Lock()

    def work(full):
        if time.time() > deadline:
            return full, "error", None
        path, content = probe_security(full)
        return full, path, content

    with ThreadPoolExecutor(int(CFG["threads_probe"])) as ex:
        for i in range(0, len(todo), 240):
            if time.time() > deadline:
                break
            chunk = todo[i:i + 240]
            nows = time.strftime("%Y-%m-%d %H:%M:%S")
            for full, path, content in ex.map(work, chunk):
                meta = names_meta.get(full) or {}
                with state_lock:
                    if isinstance(path, str):
                        state["repos_checked"][full] = {"sec_path": path, "checked_at": nows}
                        state["repos_data"][full] = {
                            "vendor": vendor, "org": org, "full_name": full,
                            "url": "https://github.com/%s" % full, "sec_path": path,
                            "stars": meta.get("stars"), "language": meta.get("language"),
                            "description": meta.get("description"), "license": meta.get("license"),
                            "first_seen": nows,
                        }
                        found += 1
                    elif path is None:
                        state["repos_checked"][full] = {"sec_path": None, "checked_at": nows}
                if isinstance(path, str) and content:
                    try:
                        d = VDIR / safe_name(vendor) / full.replace("/", "__")
                        d.mkdir(parents=True, exist_ok=True)
                        (d / "SECURITY.md").write_bytes(content)
                    except Exception as e:
                        log("内容写盘失败 %s: %s" % (full, e))
            save_state(state)
            log("%s: 探测进度 %d/%d（累计命中 %d）" % (org, min(i + 240, len(todo)), len(todo), found))
    return found


# ---------------------------------------------------------------- html 模式主扫
def sweep_html(state, org2vendor, deadline, force):
    orgs = sorted(org2vendor.keys(),
                  key=lambda o: (state["orgs"].get(o, {}).get("last_swept") is not None,
                                 state["orgs"].get(o, {}).get("last_swept") or 0, o))
    for idx, org in enumerate(orgs):
        if time.time() > deadline:
            log("预算用尽，剩余 %d 个组织下轮继续" % (len(orgs) - idx))
            break
        ent = state["orgs"].get(org) or {}
        vendor = org2vendor[org]
        fresh = (not force) and ent.get("last_swept") and \
                (time.time() - ent["last_swept"] < CFG["org_resweep_hours"] * 3600)
        try:
            if fresh:
                pending = [f for f in (ent.get("pending") or []) if f not in state["repos_checked"]]
                if not pending:
                    continue
                cache = load_meta_cache(org)
                names_meta = {f: cache.get(f, {}) for f in pending}
                log("[跳过重列] %s(%s) 处理遗留待探测 %d 个" % (org, vendor, len(pending)))
            else:
                items, kind = list_repos_any(org)
                if items is None and kind == "skip":
                    log("[限流跳过] %s API 配额不足，本轮不计失败，下轮重试" % org)
                    continue
                if items is None:
                    ent["fail_count"] = ent.get("fail_count", 0) + 1
                    ent["failed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    ent["failed_at_ts"] = time.time()
                    state["orgs"][org] = ent
                    save_state(state)
                    log("[失败] %s 列表抓取失败(第%d次)，下轮重试" % (org, ent["fail_count"]))
                    continue
                save_meta_cache(org, items)
                ent.update({"last_swept": time.time(), "repo_count": len(items), "kind": kind,
                            "fail_count": 0})
                names_meta = items
                # 元数据回填：已收录仓库补/更新星数、语言、描述、license
                for full, meta in items.items():
                    rec = state["repos_data"].get(full)
                    if rec is not None and meta:
                        for k in ("stars", "language", "description", "license"):
                            v = meta.get(k)
                            if v and rec.get(k) != v:
                                rec[k] = v
                log("[列表] %s(%s) via %s：%d 个仓库" % (org, vendor, kind, len(items)))
            probe_and_record(state, org, vendor, names_meta, deadline)
            ent["pending"] = [f for f in names_meta if f not in state["repos_checked"]]
            state["orgs"][org] = ent
            save_state(state)
        except Exception as e:
            import traceback
            log("[异常] org=%s: %s\n%s" % (org, e, traceback.format_exc()))


# ---------------------------------------------------------------- search 模式（有 token 时）
def sweep_search(state, org2vendor, deadline, token):
    swept = state.setdefault("search_swept", {})
    orgs = sorted(org2vendor.keys(), key=lambda o: (o in swept, swept.get(o) or 0, o))
    for idx, org in enumerate(orgs):
        if time.time() > deadline:
            log("预算用尽，剩余 %d 个组织下轮继续" % (len(orgs) - idx))
            break
        qualifier = "org"
        page, hits, total = 1, [], 0
        while True:
            if time.time() > deadline:
                break
            q = quote("%s:%s filename:SECURITY.md" % (qualifier, org))
            st, body = http_get("https://api.github.com/search/code?q=%s&per_page=100&page=%d" % (q, page),
                                "api", timeout=25, token=token)
            if st in (403, 429):
                time.sleep(70)
                continue
            if st == 422 and qualifier == "org":
                qualifier, page, hits = "user", 1, []
                continue
            if st != 200:
                log("[search失败] %s status=%s" % (org, st))
                break
            try:
                data = json.loads(body.decode("utf-8", "replace"))
            except Exception:
                break
            items = data.get("items", [])
            total = data.get("total_count", 0)
            for it in items:
                repo = it.get("repository") or {}
                full = repo.get("full_name")
                if full:
                    hits.append((full, it.get("path") or "SECURITY.md", repo))
            if len(hits) >= min(total, 1000) or not items:
                break
            page += 1
        if hits:
            per_repo = {}
            metas = {}
            for full, path, repo in hits:
                if full not in per_repo or path.count("/") < per_repo[full].count("/"):
                    per_repo[full] = path
                metas[full] = {"stars": repo.get("stargazers_count"),
                               "language": repo.get("language"),
                               "description": repo.get("description")}
            names_meta = {full: metas[full] for full in per_repo}
            dl_missing = []
            nows = time.strftime("%Y-%m-%d %H:%M:%S")
            for full, path in per_repo.items():
                state["repos_checked"][full] = {"sec_path": path, "checked_at": nows}
                if full not in state["repos_data"]:
                    dl_missing.append(full)
                meta = metas[full]
                state["repos_data"][full] = {
                    "vendor": org2vendor[org], "org": org, "full_name": full,
                    "url": "https://github.com/%s" % full, "sec_path": path,
                    "stars": meta.get("stars"), "language": meta.get("language"),
                    "description": meta.get("description"), "first_seen": nows,
                }

            def dl(full):
                st, body = http_get("https://raw.githubusercontent.com/%s/HEAD/%s"
                                    % (full, per_repo[full]), "raw", timeout=20)
                return full, body if st == 200 else None

            with ThreadPoolExecutor(int(CFG["threads_download"])) as ex:
                for full, content in ex.map(dl, dl_missing):
                    if content:
                        try:
                            d = VDIR / safe_name(org2vendor[org]) / full.replace("/", "__")
                            d.mkdir(parents=True, exist_ok=True)
                            (d / "SECURITY.md").write_bytes(content)
                        except Exception as e:
                            log("内容写盘失败 %s: %s" % (full, e))
            log("[search] %s: %d 个仓库含 SECURITY.md" % (org, len(per_repo)))
        swept[org] = time.time()
        state["orgs"][org] = state["orgs"].get(org) or {"last_swept": time.time()}
        state["orgs"][org]["last_swept"] = time.time()
        if total > 1000:
            state["orgs"][org]["truncated"] = True
        save_state(state)


# ---------------------------------------------------------------- 输出
def write_outputs(state, mode):
    vendors = json.loads((ASSETS / "vendors.json").read_text(encoding="utf-8"))
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    per = {}
    for full, m in state["repos_data"].items():
        per.setdefault(m.get("vendor") or m["org"], []).append(m)
    csv_rows = []
    vstats = []
    for v in vendors:
        name = v["vendor"]
        safe = safe_name(name)
        folder = VDIR / safe
        folder.mkdir(parents=True, exist_ok=True)
        repos = sorted(per.get(name, []), key=lambda r: -(r.get("stars") or 0))
        (folder / "repos.json").write_text(
            json.dumps(repos, ensure_ascii=False, indent=1), encoding="utf-8")
        lines = [
            "# %s（%s）— 开源项目 SECURITY.MD 清单" % (name, v.get("src") or "未知SRC"),
            "",
            "- 收录仓库数：**%d**（均含 SECURITY.md，原文在 %s/ 下按仓库存放）" % (len(repos), safe),
            "- GitHub 组织：%s" % ("、".join(v["orgs"]) or "（无）"),
            "- 更新时间：%s" % now,
            "",
            "| 仓库（GitHub 项目页） | 星数 | 语言 | SECURITY.md（本地文本） | 项目链接 |",
            "|---|---:|---|---|---|",
        ]
        for r in repos:
            lines.append("| %s | %s | %s | %s | %s |" % (
                r["full_name"],
                r.get("stars") if r.get("stars") is not None else "-",
                r.get("language") or "-",
                r.get("sec_path"),
                r["url"]))
        (folder / "清单.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        for r in repos:
            csv_rows.append([name, v.get("src", ""), r["org"], r["full_name"], r["url"],
                             r.get("stars", ""), r.get("language", ""), r.get("sec_path", ""),
                             (r.get("description") or "")])
        vstats.append({"vendor": name, "src": v.get("src", ""), "orgs": v["orgs"],
                       "sec_repos": len(repos)})
    with open(INDEX / "总表.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["厂商", "SRC", "组织", "仓库", "链接", "星数", "语言", "SECURITY.md", "描述"])
        w.writerows(csv_rows)
    swept = sum(1 for o, e in state["orgs"].items() if e.get("last_swept"))
    failed = sorted(o for o, e in state["orgs"].items()
                    if e.get("fail_count") and not e.get("repo_count")
                    and (time.time() - e.get("failed_at_ts", 0) < 2700))
    stats = {
        "generated_at": now,
        "mode": mode,
        "totals": {
            "vendors": len(vendors),
            "orgs": len({o for v in vendors for o in v["orgs"]}),
            "orgs_swept": swept,
            "sec_repos": len(state["repos_data"]),
            "negative_cached": sum(1 for x in state["repos_checked"].values() if x.get("sec_path") is None),
        },
        "vendors": vstats,
        "orgs_failed": failed,
    }
    (INDEX / "统计.json").write_text(json.dumps(stats, ensure_ascii=False, indent=1), encoding="utf-8")
    write_index_html(stats, state)
    return stats


def write_index_html(stats, state):
    from build_dashboard import build_dashboard
    build_dashboard(BASE, stats, state["repos_data"].values())


# ---------------------------------------------------------------- 主流程
def main():
    try:
        import faulthandler
        faulthandler.enable(open(SCRIPTS / "collect_faults.log", "a", encoding="utf-8"))
    except Exception:
        pass
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=None, help="本次运行最长秒数")
    ap.add_argument("--force", action="store_true", help="忽略组织列表缓存强制重扫")
    args = ap.parse_args()
    for d in (BASE, SCRIPTS, ASSETS, INDEX, VDIR):
        d.mkdir(parents=True, exist_ok=True)
    if not acquire_lock():
        log("另一收集实例运行中（collect.lock 存活），本轮跳过。")
        return
    t0 = time.time()
    budget = args.budget or int(CFG["run_budget_sec"])
    try:
        token = find_token()
        mode = "search"
        if token:
            q = quote("org:github filename:SECURITY.md")
            st, _ = http_get("https://api.github.com/search/code?q=%s&per_page=1" % q,
                             "api", timeout=20, token=token)
            if st in (401, 403):
                token, mode = None, "html"
        else:
            mode = "html"
        log("===== 启动：mode=%s token=%s budget=%ds =====" % (mode, "有" if token else "无", budget))
        vendors, org2vendor = merge_vendors()
        state = load_state()
        # 清理 state 中已改名/已移除组织的残留条目（否则失败名单永远挂着旧名）
        stale = [o for o in state["orgs"] if o not in org2vendor]
        for o in stale:
            state["orgs"].pop(o, None)
            state["search_swept"].pop(o, None)
        if stale:
            log("清理残留组织状态: %s" % ", ".join(stale))
        before = len(state["repos_data"])
        deadline = t0 + budget - 90
        if mode == "search":
            sweep_search(state, org2vendor, deadline, token)
        else:
            sweep_html(state, org2vendor, deadline, args.force)
        stats = write_outputs(state, mode)
        added = len(state["repos_data"]) - before
        summary = {
            "finished_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "mode": mode,
            "duration_sec": int(time.time() - t0),
            "added_this_run": added,
            "sec_repos_total": len(state["repos_data"]),
            "vendors_total": stats["totals"]["vendors"],
            "orgs_total": stats["totals"]["orgs"],
            "orgs_swept": stats["totals"]["orgs_swept"],
            "orgs_failed": stats["orgs_failed"],
        }
        (INDEX / "last_run.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
        log("完成：%s" % json.dumps(summary, ensure_ascii=False))
    except Exception:
        import traceback
        log("致命异常:\n%s" % traceback.format_exc())
        try:
            write_outputs(load_state(), "html")
        except Exception:
            pass
        raise SystemExit(1)
    finally:
        release_lock()


if __name__ == "__main__":
    main()
