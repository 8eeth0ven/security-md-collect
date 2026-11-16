"""Verify an explicit priority-project set and import real public SECURITY.md files.

No credentials are needed. A missing standard file is not proof that a project has
no disclosure policy. Account defaults are imported once as owner/.github, never
inflated into one policy record per inheriting repository. Unknown HTTP results
remain retryable. Runtime checkpoints belong outside the publication checkout.
"""
import argparse
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlsplit

import collect

PATHS = ('.github/SECURITY.md', '.github/security.md', 'SECURITY.md',
         'security.md', 'Security.md', 'docs/SECURITY.md', 'docs/security.md',
         'SECURITY.MD', '.github/SECURITY.MD', 'docs/SECURITY.MD')


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def get(url, timeout=12):
    # Direct public reads do not inherit potentially credential-bearing user
    # proxy settings. The collector itself retains its configurable transports.
    req = urllib.request.Request(url, headers={'User-Agent': 'security-md-priority-audit/1.0'})
    try:
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=timeout) as response:
            body = response.read(4 * 1024 * 1024)
            return {'url': url, 'resolved_url': response.url, 'status': response.status,
                    'checked_at': timestamp(), 'body': body}
    except urllib.error.HTTPError as exc:
        return {'url': url, 'resolved_url': exc.url, 'status': exc.code, 'checked_at': timestamp(), 'body': b''}
    except (OSError, TimeoutError, urllib.error.URLError):
        return {'url': url, 'resolved_url': url, 'status': 0, 'checked_at': timestamp(), 'body': b''}


def probe(repo, preferred=(), retries=1):
    checks = []
    paths = list(dict.fromkeys([*preferred, *PATHS]))
    for path in paths:
        url = 'https://raw.githubusercontent.com/%s/HEAD/%s' % (repo, quote(path, safe='/'))
        for attempt in range(retries + 1):
            response = get(url)
            if response['status'] not in (0, 429, 500, 502, 503, 504):
                break
            if attempt < retries:
                time.sleep(0.4 * (attempt + 1))
        body = response.pop('body')
        checks.append(response)
        if response['status'] == 200 and body.strip():
            return {'repo': repo, 'status': 'policy_found', 'path': path,
                    'source_url': url, 'sha256': hashlib.sha256(body).hexdigest(),
                    'checked_at': timestamp(), 'checks': checks}, body
    complete = all(row['status'] == 404 for row in checks)
    return {'repo': repo, 'status': 'no_standard_policy' if complete else 'unresolved',
            'checked_at': timestamp(), 'checks': checks}, None


def valid_repo(value):
    return bool(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_.-]+', value))


def read_existing(base):
    return {row['full_name'].casefold(): row for file in (base/'厂商').glob('*/repos.json')
            for row in json.loads(file.read_text(encoding='utf-8'))}


def write_imports(base, imports, manifest):
    """Only touch positive policy records, their original text, and vendor maps."""
    by_project = {entry['repo'].casefold(): entry for entry in manifest}
    vendors = json.loads((base/'资产/vendors.json').read_text(encoding='utf-8'))
    owner_vendor = {owner.casefold(): row['vendor'] for row in vendors for owner in row['orgs']}
    mapping_path = base/'资产/厂商映射-重点项目.json'
    extra_mapping = json.loads(mapping_path.read_text(encoding='utf-8')) if mapping_path.exists() else []
    new_owners = defaultdict(set)
    project_owner_vendor = {}
    for project in manifest:
        project_owner_vendor.setdefault(project['repo'].split('/')[0].casefold(), project['vendor'])
    for row, body in imports:
        owner = row['repo'].split('/')[0]
        if owner.casefold() not in owner_vendor:
            vendor = project_owner_vendor.get(owner.casefold(), owner)
            owner_vendor[owner.casefold()] = vendor
            new_owners[vendor].add(owner)
    for vendor, owners in sorted(new_owners.items()):
        extra_mapping.append({'vendor': vendor, 'src': '无（重点开源项目政策发现）', 'orgs': sorted(owners),
                              'unverified': [], 'note': '仅作为公开安全政策归属，不代表赏金范围；逐项证据见 索引/重点项目核查.json。'})
    if new_owners:
        atomic_json(mapping_path, extra_mapping)
        # Merge using the same precedence rules as the regular collector.
        collect.merge_vendors()
        vendors = json.loads((base/'资产/vendors.json').read_text(encoding='utf-8'))
        owner_vendor = {owner.casefold(): row['vendor'] for row in vendors for owner in row['orgs']}
    touched = set()
    per_vendor = {}
    for row, body in imports:
        full = row['repo']
        owner = full.split('/')[0]
        vendor = owner_vendor[owner.casefold()]
        folder = base/'厂商'/collect.safe_name(vendor)
        path = folder/'repos.json'
        if vendor not in per_vendor:
            per_vendor[vendor] = {r['full_name'].casefold(): r for r in json.loads(path.read_text(encoding='utf-8'))} if path.exists() else {}
        project = by_project.get(full.casefold(), {})
        aliases = [urlsplit(url).path.strip('/').casefold() for url in project.get('previous_repository_urls', [])]
        previous = per_vendor[vendor].get(full.casefold(), {})
        for alias in aliases:
            historical = per_vendor[vendor].pop(alias, None)
            if historical and not previous:
                previous = historical
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        record = {**previous, 'vendor': vendor, 'org': owner, 'full_name': full,
                  'url': 'https://github.com/'+full, 'sec_path': row['path'],
                  'stars': previous.get('stars'), 'language': previous.get('language'),
                  'description': previous.get('description') or project.get('name') or 'Account default security policy',
                  'license': previous.get('license'), 'first_seen': previous.get('first_seen') or now,
                  'last_verified': now}
        per_vendor[vendor][full.casefold()] = record
        destination = folder/full.replace('/', '__')/'SECURITY.md'
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(body)
        touched.add(vendor)
    vendor_map = {v['vendor']: v for v in vendors}
    for vendor in touched:
        rows = sorted(per_vendor[vendor].values(), key=lambda r: (-(r.get('stars') or 0), r['full_name'].casefold()))
        folder = base/'厂商'/collect.safe_name(vendor)
        atomic_json(folder/'repos.json', rows)
        src = vendor_map[vendor].get('src') or '未知SRC'
        lines = ['# %s（%s）— 开源项目 SECURITY.MD 清单' % (vendor, src), '',
                 '- 收录仓库数：**%d**（均含 SECURITY.md，原文在 %s/ 下按仓库存放）' % (len(rows), collect.safe_name(vendor)),
                 '- GitHub 组织：'+ '、'.join(vendor_map[vendor]['orgs']), '- 更新时间：'+time.strftime('%Y-%m-%d %H:%M:%S'), '',
                 '| 仓库（GitHub 项目页） | 星数 | 语言 | SECURITY.md（本地文本） | 项目链接 |', '|---|---:|---|---|---|']
        for r in rows:
            lines.append('| %s | %s | %s | %s | %s |' % (r['full_name'], r.get('stars') if r.get('stars') is not None else '-', r.get('language') or '-', r['sec_path'], r['url']))
        (folder/'清单.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    return sorted(touched)


def run(args):
    base = args.base.resolve()
    # collect uses this module's configured BASE for vendor merging and lock.
    if base != collect.BASE.resolve():
        raise ValueError('Set SECMD_BASE to --base before running against a different data root')
    projects = json.loads(args.manifest.read_text(encoding='utf-8'))['projects']
    if not projects or len({r['repo'].casefold() for r in projects}) != len(projects):
        raise ValueError('Priority manifest must contain unique explicit repositories')
    if any(not valid_repo(r['repo']) for r in projects):
        raise ValueError('Unsafe repository identifier')
    existing = read_existing(base)
    checkpoint = args.checkpoint.resolve()
    checkpoint.mkdir(parents=True, exist_ok=True)
    baseline_path = checkpoint/'baseline-index.json'
    if not baseline_path.exists():
        atomic_json(baseline_path, {'generated_at': timestamp(), 'repos': [r['full_name'] for r in existing.values()]})
    baseline_records = json.loads(baseline_path.read_text(encoding='utf-8'))['repos']
    baseline = {name.casefold() for name in baseline_records}
    def was_indexed(project):
        identities = {project['repo'].casefold(), *[urlsplit(url).path.strip('/').casefold() for url in project.get('previous_repository_urls', [])]}
        return bool(identities & baseline)
    if not collect.acquire_lock():
        raise RuntimeError('Collector lock is active; retry after the writer finishes')
    results = {}
    imports = []
    try:
        def work(project):
            repo = project['repo']
            cache = checkpoint/(repo.replace('/', '__')+'.json')
            content_file = checkpoint/(repo.replace('/', '__')+'.md')
            if not args.refresh and cache.exists():
                old = json.loads(cache.read_text(encoding='utf-8'))
                if old['status'] != 'unresolved' and (old['status'] != 'policy_found' or content_file.exists()):
                    return old, content_file.read_bytes() if old['status'] == 'policy_found' else None
            previous = existing.get(repo.casefold(), {})
            row, body = probe(repo, [previous['sec_path']] if previous.get('sec_path') else (), args.retries)
            # A complete absence test requires a live repository, not just raw 404s.
            if row['status'] == 'no_standard_policy':
                page = get('https://github.com/'+repo)
                page.pop('body')
                row['repository_check'] = page
                if page['status'] != 200:
                    row['status'] = 'unresolved' if page['status'] != 404 else 'repository_unavailable'
                else:
                    parts = urlsplit(page['resolved_url']).path.strip('/').split('/')
                    if len(parts) == 2 and valid_repo('/'.join(parts)):
                        row['canonical_repo'] = '/'.join(parts)
            atomic_json(cache, row)
            if body:
                content_file.write_bytes(body)
            return row, body
        with ThreadPoolExecutor(args.threads) as pool:
            futures = {pool.submit(work, project): project['repo'] for project in projects}
            for future in as_completed(futures):
                row, body = future.result()
                results[row['repo']] = row
                if body:
                    imports.append((row, body))
                if len(results) % 10 == 0 or len(results) == len(projects):
                    print('priority %d/%d %s' % (len(results), len(projects), dict(Counter(r['status'] for r in results.values()))), flush=True)
        # Probe one default-policy repository for every owner. A failed repo
        # policy request is not converted to absent merely because defaults exist.
        owners = sorted({p['repo'].split('/')[0] for p in projects})
        defaults = {}
        with ThreadPoolExecutor(args.threads) as pool:
            futures = {pool.submit(work, {'repo': owner+'/.github'}): owner for owner in owners}
            for future in as_completed(futures):
                row, body = future.result()
                defaults[futures[future]] = row
                if body:
                    imports.append((row, body))
        report_rows = []
        for project in projects:
            row = results[project['repo']]
            default = defaults[project['repo'].split('/')[0]]
            row = {**project, **row, 'previously_indexed': was_indexed(project),
                   'default_policy_status': default['status']}
            if row['status'] == 'policy_found':
                row['result'] = 'indexed_verified' if row['previously_indexed'] else 'added'
            elif row['status'] == 'no_standard_policy' and default['status'] == 'policy_found':
                row['result'] = 'default_policy_available'
                row['default_policy_repo'] = default['repo']
                row['default_policy_url'] = default['source_url']
            elif row['status'] == 'no_standard_policy' and default['status'] in ('no_standard_policy', 'repository_unavailable'):
                row['result'] = 'no_standard_policy'
            else:
                row['result'] = 'unresolved'
            report_rows.append(row)
        public_defaults = [{**row, 'previously_indexed': row['repo'].casefold() in baseline} for row in defaults.values()]
        unique_imports = {row['repo'].casefold(): (row, body) for row, body in imports}
        new_direct = sum(row['status'] == 'policy_found' and not row['previously_indexed'] for row in report_rows)
        new_defaults = sum(row['status'] == 'policy_found' and not row['previously_indexed'] for row in public_defaults)
        report = {'schema_version': 1, 'generated_at': timestamp(), 'projects': len(projects),
                  'result_counts': dict(Counter(r['result'] for r in report_rows)),
                  'added_direct_policies': new_direct, 'added_default_policies': new_defaults,
                  'remaining': [r['repo'] for r in report_rows if r['result'] == 'unresolved'],
                  'remaining_account_defaults': [r['repo'] for r in public_defaults if r['status'] == 'unresolved'],
                  'baseline_indexed_policies': len(baseline_records),
                  'baseline_unique_repositories': len(baseline),
                  'historical_unchecked': {'reported_count': 221, 'identity_available': False,
                                          'status': 'unresolved', 'reason': 'Original collector state and org catalog are not distributed in the public repository; this run does not claim to clear the historical 221.'},
                  'limits': ['This explicit priority set is not all open source projects or bounty scope.',
                             'no_standard_policy means all listed Markdown candidate paths returned 404 in a live repository; external disclosure pages and other formats may exist.',
                             'Account defaults are counted once as owner/.github, not expanded into per-project document counts.',
                             'Transport failures remain unresolved and are retried on the next invocation.'],
                  'rows': report_rows, 'account_defaults': public_defaults}
        if args.apply:
            report['touched_vendors'] = write_imports(base, list(unique_imports.values()), projects)
        atomic_json(base/'索引/重点项目核查.json', report)
        atomic_json(base/'索引/待核仓库.json', {
            'generated_at': report['generated_at'], 'source': '重点项目核查.json',
            'repositories': report['remaining'], 'account_defaults': report['remaining_account_defaults'],
            'historical_unchecked': report['historical_unchecked'],
            'resume': 'Run audit_priority_projects.py with the same private checkpoint directory; completed HTTP checks are reused and unresolved checks are retried.'})
        atomic_json(checkpoint/'summary.json', {k:v for k,v in report.items() if k not in ('rows', 'account_defaults')})
        print(json.dumps({k:v for k,v in report.items() if k not in ('rows','account_defaults','touched_vendors')}, ensure_ascii=False), flush=True)
    finally:
        collect.release_lock()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=collect.BASE)
    parser.add_argument('--manifest', type=Path, default=collect.ASSETS/'重点项目.json')
    parser.add_argument('--checkpoint', required=True, type=Path, help='Private run cache outside the publication checkout')
    parser.add_argument('--threads', type=int, default=12)
    parser.add_argument('--retries', type=int, default=1)
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--apply', action='store_true')
    arguments = parser.parse_args()
    if not 1 <= arguments.threads <= 24:
        parser.error('--threads must be between 1 and 24')
    if arguments.checkpoint.resolve().is_relative_to(arguments.base.resolve()):
        parser.error('Checkpoint cache must stay outside the public checkout')
    run(arguments)
