"""Build the portable Pages dashboard from public snapshots; no network or token required."""
import argparse
import json
import os
import re
import shutil
from pathlib import Path
from urllib.parse import quote


def safe_name(name):
    return re.sub(r'[\\/:*?"<>|\r\n\t]', '_', str(name)).strip().strip('.') or '_unnamed'


def atomic_text(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(content, encoding='utf-8')
    temporary.replace(path)


def build_dashboard(base, stats=None, records=None):
    base = Path(base).resolve()
    if stats is None:
        stats = json.loads((base / '索引/统计.json').read_text(encoding='utf-8'))
    if records is None:
        records = []
        for file in sorted((base / '厂商').glob('*/repos.json')):
            records.extend(json.loads(file.read_text(encoding='utf-8')))
    sources = {v['vendor']: v.get('src', '') for v in stats['vendors']}
    repos = []
    for record in sorted(records, key=lambda r: r['full_name'].lower()):
        vendor = record.get('vendor') or record['org']
        local = Path('厂商') / safe_name(vendor) / record['full_name'].replace('/', '__') / 'SECURITY.md'
        repos.append({
            'v': vendor, 'f': record['full_name'], 'src': sources.get(vendor, ''),
            's': record.get('stars'), 'l': record.get('language') or '',
            'lic': record.get('license') or '', 'd': record.get('description') or '',
            'path': record.get('sec_path') or 'SECURITY.md',
            'loc': quote(local.as_posix(), safe='/') if (base / local).is_file() else None,
        })
    payload = {'stats': stats, 'repos': repos}
    atomic_text(base / '索引/dashboard.json', json.dumps(payload, ensure_ascii=False, separators=(',', ':')) + '\n')
    template = Path(__file__).with_name('dashboard.html').read_text(encoding='utf-8')
    source = Path(__file__).resolve().parents[1]
    if source != base:
        shutil.copytree(source / 'web', base / 'web', dirs_exist_ok=True)
    atomic_text(base / 'index.html', template)
    # Old local bookmarks keep working, while every asset resolves from the project root.
    atomic_text(base / '索引/index.html', '<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
                '<meta http-equiv="refresh" content="0;url=../index.html">'
                '<title>SECURITY.md Collect</title><a href="../index.html">打开看板 / Open dashboard</a></html>\n')
    return len(repos)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=Path(os.environ.get('SECMD_BASE') or Path(__file__).resolve().parents[1]))
    args = parser.parse_args()
    print('Dashboard built: %s repositories' % build_dashboard(args.base))
