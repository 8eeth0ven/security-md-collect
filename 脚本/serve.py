# -*- coding: utf-8 -*-
"""局域网静态看板服务：把收集成果目录暴露在 0.0.0.0:{port}（默认 8899）

- /            -> 直接返回 索引/index.html（看板，无跳转）
- /status      -> 返回 索引/统计.json（供定时任务探活与其它 Agent 调用）
- 其余路径     -> 静态文件 / 目录浏览（厂商清单、各仓库 SECURITY.md 原文）

注意：用 python.exe 运行（不要用 pythonw）——Windows 防火墙按程序放行，
本机只放行了 python.exe 的入站，pythonw 会被局域网拦截。
"""
import json
import sys
import time
import traceback
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = Path(os.environ.get("SECMD_BASE") or (Path.home() / "Desktop" / "大厂开源SECURITY_MD收集"))
CFG = BASE / "脚本" / "config.json"
LOG = BASE / "脚本" / "serve.log"

try:
    _cfg = json.loads(CFG.read_text(encoding="utf-8")).get("port", 8899)
    PORTS = sorted({8899, 8000, 8080, int(_cfg)})  # 多端口对照：排查防火墙/路由器按端口拦截
except Exception:
    PORTS = [8899, 8000, 8080]


def slog(msg):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write("[%s] %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
    except Exception:
        pass


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(BASE), **kw)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            try:
                body = (BASE / "索引" / "index.html").read_bytes()
            except Exception:
                body = "<meta charset=utf-8>看板尚未生成，等收集器跑完第一轮。".encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path == "/status":
            try:
                body = (BASE / "索引" / "统计.json").read_bytes()
            except Exception:
                body = b'{"error": "stats not ready"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    import threading
    servers = []
    for p in PORTS:
        try:
            srv = ThreadingHTTPServer(("0.0.0.0", p), Handler)
            servers.append((p, srv))
        except OSError as e:
            slog("绑定 0.0.0.0:%d 失败: %s" % (p, e))
    if not servers:
        slog("所有端口绑定失败，退出")
        raise SystemExit(1)
    slog("启动: pid=%s, 端口=%s, root=%s" % (sys.executable, [p for p, _ in servers], BASE))
    print("serving %s on %s" % (BASE, [p for p, _ in servers]), flush=True)
    try:
        threads = [threading.Thread(target=s.serve_forever, daemon=True) for _, s in servers]
        for t in threads:
            t.start()
        while True:
            time.sleep(3600)
    except Exception:
        slog("异常退出:\n%s" % traceback.format_exc())
        raise
