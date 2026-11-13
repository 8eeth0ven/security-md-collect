"""Serve the public dashboard on localhost. Use --host 0.0.0.0 to share on a LAN."""
import argparse
import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

BASE = Path(os.environ.get('SECMD_BASE') or Path(__file__).resolve().parents[1]).resolve()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE), **kwargs)

    def send_head(self):
        path = unquote(urlsplit(self.path).path)
        if path == '/status':
            self.path = '/索引/统计.json'
            path = self.path
        parts = Path(path.lstrip('/')).parts
        target = (BASE / path.lstrip('/')).resolve()
        allowed = (
            path in ('/', '/index.html', '/README.md', '/prompt-给其他Agent.md')
            or (parts and parts[0] in ('厂商', '赏金APK', 'web'))
            or (len(parts) == 2 and parts[0] == '索引' and parts[1] in
                ('dashboard.json', '统计.json', '总表.csv', 'index.html', 'retry-candidates.json'))
            or (len(parts) >= 3 and parts[:2] == ('docs', 'assets'))
        )
        if (not allowed or not target.is_relative_to(BASE)
                or any(part.startswith('.') for part in parts)
                or (target.is_dir() and path != '/')):
            self.send_error(404, 'Not found')
            return None
        return super().send_head()

    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('X-Content-Type-Options', 'nosniff')
        super().end_headers()


def main():
    try:
        config = json.loads((BASE / '脚本/config.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        config = {}
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default=config.get('host', '127.0.0.1'))
    parser.add_argument('--port', type=int, default=int(config.get('port', 8899)))
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print('Serving %s at http://%s:%s' % (BASE, args.host, args.port), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
