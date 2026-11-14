"""Refresh public Android scope metadata, preserving unobserved historical records.

No APK downloads or target probing. Upstream absence is never an out-of-scope verdict.
Use --source-dir for a reproducible offline import of revision.json + platform.json.
"""
import argparse
import hashlib
import json
import re
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import requests

from build_apk_board import PACKAGE, PLATFORMS, normalize, safe_url, write

UPSTREAM = 'https://github.com/arkadiyt/bounty-targets-data'
NAMES = {'h1': 'hackerone', 'bugcrowd': 'bugcrowd', 'ywh': 'yeswehack', 'intigriti': 'intigriti'}


def stamp():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def get_json(url, proxy=None):
    proxies = {'https': proxy, 'http': proxy} if proxy else None
    for attempt in range(3):
        try:
            response = requests.get(url, proxies=proxies, timeout=40,
                                    headers={'User-Agent': 'security-md-collect/public-metadata'})
            response.raise_for_status()
            return response.json(), response.content
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(attempt+1)


def package_from(value):
    """Only a complete Play URL or complete package identifier; never prose or hosts."""
    value = str(value or '').strip()
    try:
        parsed = urlsplit(value)
    except ValueError:
        return ''
    if ((parsed.hostname == 'play.google.com' and parsed.path == '/store/apps/details')
            or (parsed.hostname == 'market.android.com' and parsed.path == '/details')):
        candidate = parse_qs(parsed.query).get('id', [''])[0]
        return candidate if PACKAGE.fullmatch(candidate) else ''
    # The caller only supplies bare values from explicitly typed Android scope rows.
    return value if PACKAGE.fullmatch(value) else ''


def android_target(target):
    kind = (target.get('type') or target.get('asset_type') or '').lower()
    value = str(target.get('endpoint') or target.get('target') or target.get('asset_identifier') or '')
    try:
        parsed = urlsplit(value)
    except ValueError:
        parsed = urlsplit('')
    return (kind in ('android', 'mobile-application-android', 'google_play_app_id', 'other_apk')
            or (parsed.hostname == 'play.google.com' and parsed.path == '/store/apps/details')
            or (kind == 'mobile-application' and bool(re.search(r'\bandroid\b|\.apk(?:[?#]|$)', value, re.I))))


def convert(platform, program, target):
    value = str(target.get('endpoint') or target.get('target') or target.get('asset_identifier') or '').strip()
    uri = safe_url(target.get('uri')) or safe_url(value)
    kind = target.get('type') or target.get('asset_type') or ''
    package = package_from(uri) if uri and urlsplit(uri).hostname == 'play.google.com' else package_from(value)
    # Intigriti Android rows may label the concrete app link in their own description.
    # Never harvest links from a generic scope/program description or exclusion list.
    app_link = ''
    description = str(target.get('description') or '').replace('\\n', '\n').replace('\\xa0', ' ')
    if not package and kind == 'android' and not re.search(r'exclud|out.of.scope|排除|不在范围', description, re.I):
        links = re.findall(r'^\s*App\s*link:\s*(?:App Link\s+)?(https?://play\.google\.com/store/apps/details\?[^\s<>"\)]+)', description, re.I | re.M)
        if len(set(links)) == 1 and package_from(links[0]):
            app_link = links[0]
            package = package_from(app_link)
    common = {'name': program.get('name'), 'target': value, 'uri': uri or None, 'apk_direct': None, 'play': None,
              'package': package or None, 'package_source': 'Play链接' if package and uri and urlsplit(uri).hostname == 'play.google.com' else 'scope包名' if package else None,
              'scope_type': kind, 'in_scope': True}
    if app_link:
        common.update(play=app_link, package_source='scope应用链接', package_evidence=description)
    if uri and re.search(r'\.apk(?:$|[?#])', uri, re.I):
        common['apk_direct'] = uri
    if platform == 'h1':
        common.update(handle=program['handle'], offers_bounties=program.get('offers_bounties'),
                      eligible_for_bounty=target.get('eligible_for_bounty'),
                      eligible_for_submission=target.get('eligible_for_submission'),
                      archived=target.get('archived', False), submission_state=program.get('submission_state'),
                      asset_type=kind)
    elif platform == 'bugcrowd':
        common.update(handle=program['url'].rstrip('/').split('/')[-1], program=program['name'],
                      bounty_type='cash' if (program.get('max_payout') or 0) > 0 else 'unknown',
                      reward=str(program.get('max_payout') or ''), state=program.get('state'))
    elif platform == 'ywh':
        common.update(slug=program['id'], bounty_type='bounty' if (program.get('max_bounty') or 0) > 0 else 'vdp',
                      reward=str(program.get('max_bounty') or ''), archived=program.get('disabled', False))
    else:
        max_reward = (program.get('max_bounty') or {}).get('value') or 0
        impact = target.get('impact')
        eligible = max_reward > 0 and bool(impact) and str(impact).lower() != 'no bounty'
        common.update(handle=program['handle'], company=program.get('company_handle'),
                      program_url=program.get('url'), bounty_type='bounty' if eligible else 'vdp' if impact == 'No Bounty' or max_reward == 0 else 'unknown',
                      eligible_for_bounty=eligible, reward=str(max_reward), impact=impact,
                      status=program.get('status'))
    return common


def identity(platform, row):
    handle = str(row.get('handle') or row.get('slug') or '').casefold()
    company = str(row.get('company') or '').casefold() if platform == 'intigriti' else ''
    # Raw scope identity retains separate targets even if the same package is repeated.
    target = str(row.get('target') or '').strip().rstrip('/').casefold()
    for value in (row.get('uri'), row.get('target')):
        if value and urlsplit(safe_url(value)).hostname == 'play.google.com' and package_from(value):
            target = 'play:' + package_from(value).casefold()
            break
    return (company, handle, target)


def merge(platform, previous, incoming, provenance):
    merged = []
    for old in previous:
        record = dict(old)
        record['scope_observation'] = 'historical'
        record.setdefault('scope_observed_at', '2026-11-13')
        record.setdefault('scope_source', normalize(platform, record)['url'])
        # The old Intigriti preview was a description clue, not an actual scope row.
        if platform == 'intigriti' and record.get('clue_kind'):
            continue
        merged.append(record)
    by_identity = {identity(platform, row): row for row in merged}
    merged = list(by_identity.values())
    added = 0
    for row in incoming:
        key = identity(platform, row)
        old = by_identity.get(key)
        if old is None:
            old = {}
            merged.append(old)
            added += 1
        # Preserve separately curated package mappings only as explicitly unverified hints.
        curated = {k: old[k] for k in ('package', 'package_source', 'play', 'apkpure_apk', 'apkpure_xapk')
                   if k in old} if not row.get('package') else {}
        for key in ('play', 'apkpure_apk', 'apkpure_xapk'):
            old.pop(key, None)
        old.update(row)
        old.update(curated)
        old.update(provenance, scope_observation='observed')
        by_identity[key] = old
    return merged, added


def official_ywh(proxy=None):
    programs, sources = [], []
    page = 1
    while True:
        url = 'https://api.yeswehack.com/programs?page=%s' % page
        data, body = get_json(url, proxy)
        sources.append({'url': url, 'sha256': hashlib.sha256(body).hexdigest()})
        programs.extend(data['items'])
        if page >= data['pagination']['nb_pages']:
            if len(programs) != data['pagination']['nb_results']:
                raise ValueError('YesWeHack pagination changed during collection; retry')
            break
        page += 1
    def detail(program):
        url = 'https://api.yeswehack.com/programs/' + program['slug']
        data, body = get_json(url, proxy)
        return data, {'url': url, 'sha256': hashlib.sha256(body).hexdigest(),
                      'upstream_updated_at': data.get('last_update_at')}
    details = list(ThreadPoolExecutor(4).map(detail, programs))
    rows = []
    for data, source in details:
        sources.append(source)
        if data.get('archived') or data.get('disabled'):
            continue
        for scope in data['scopes']:
            target = {'target': scope['scope'], 'type': scope['scope_type']}
            if android_target(target):
                row = convert('ywh', {'id': data['slug'], 'name': data['title'],
                              'max_bounty': data.get('bounty_reward_max') if data.get('bounty') else 0}, target)
                row['scope_source'] = source['url']
                row['asset_value'] = scope.get('asset_value')
                row['bounty_type'] = 'bounty' if data.get('bounty') else 'vdp'
                rows.append(row)
    return rows, sources, len(programs)


def update(base, source_dir=None, proxy=None, with_ywh=False, cache_dir=None):
    fetched = stamp()
    if source_dir:
        revision = json.loads((source_dir / 'revision.json').read_text(encoding='utf-8'))
    else:
        data, _ = get_json('https://api.github.com/repos/arkadiyt/bounty-targets-data/commits/main', proxy)
        revision = {'sha': data['sha'], 'committed_at': data['commit']['committer']['date']}
    if not re.fullmatch(r'[a-f0-9]{40}', revision['sha']):
        raise ValueError('A full upstream commit SHA is required')
    out = base / '赏金APK'
    planned, coverage, observations, cached = {}, [], [], {}
    official_rows, official_sources, official_count = official_ywh(proxy) if with_ywh else (None, [], None)
    for platform, _, filename, _ in PLATFORMS:
        if platform not in NAMES:
            continue
        name = NAMES[platform]
        url = 'https://raw.githubusercontent.com/arkadiyt/bounty-targets-data/%s/data/%s_data.json' % (revision['sha'], name)
        if source_dir:
            body = (source_dir / (name + '.json')).read_bytes()
            programs = json.loads(body)
        else:
            programs, body = get_json(url, proxy)
        if not isinstance(programs, list) or not programs:
            raise ValueError('Empty or invalid source: ' + name)
        cached[name+'.json'] = body
        incoming = [convert(platform, p, t) for p in programs for t in p['targets']['in_scope'] if android_target(t)]
        if platform == 'ywh' and official_rows is not None:
            incoming = official_rows
        source = {'scope_observed_at': fetched, 'scope_source': url, 'source_revision': revision['sha']}
        # Official individual provenance takes precedence over the aggregated source.
        for row in incoming:
            row.setdefault('scope_source', url)
        previous = json.loads((out / filename).read_text(encoding='utf-8'))
        rows, added = merge(platform, previous, incoming, {'scope_observed_at': fetched, 'source_revision': revision['sha']})
        planned[out / filename] = rows
        observations.extend(dict(row, platform=platform, **{k:v for k,v in source.items() if k not in row}) for row in incoming)
        observed = [row for row in rows if row['scope_observation'] == 'observed']
        coverage.append({'platform': platform, 'source_url': url, 'sha256': hashlib.sha256(body).hexdigest(),
                         'source_programs': official_count if platform == 'ywh' and official_count is not None else len(programs),
                         'android_scopes_in_source': len(incoming), 'observed_records': len(observed),
                         'added_records': added, 'historical_unconfirmed': len(rows)-len(observed),
                         'unresolved_packages': sum(not normalize(platform, r)['package'] for r in observed),
                         'bounty_eligible_observed': sum(normalize(platform, r)['bounty']=='cash' for r in observed)})
    report = {'fetched_at': fetched, 'upstream': UPSTREAM, 'license': 'MIT', 'revision': revision,
              'platforms': coverage, 'yeswehack_official_sources': official_sources,
              'limits': ['Public accessible scopes only; private/login/TAC/2FA scopes are not a complete universe.',
                         'A missing historical record is unconfirmed, never an out-of-scope determination.',
                         'Only typed Android scope values are parsed; description links may explicitly be excluded.',
                         'Package syntax and mirror URL generation do not verify an app, download or bounty scope.']}
    # All network/parse operations finish before modifying the public snapshot.
    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)
        for name, body in cached.items():
            (cache_dir/name).write_bytes(body)
        (cache_dir/'revision.json').write_text(json.dumps(revision), encoding='utf-8')
    for path, data in planned.items():
        write(path, json.dumps(data, ensure_ascii=False, indent=1)+'\n')
    write(out / 'source-observations.json', json.dumps(observations, ensure_ascii=False, indent=1)+'\n')
    write(out / 'coverage.json', json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    write(out / 'snapshot.json', json.dumps({'generated_at': fetched}, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--source-dir', type=Path)
    parser.add_argument('--cache-dir', type=Path, help='Save pinned public sources for later policy discovery')
    parser.add_argument('--proxy', help='Optional transport proxy; TLS verification stays enabled')
    parser.add_argument('--official-ywh', action='store_true', help='Read all public official YesWeHack scopes')
    args = parser.parse_args()
    result = update(args.base.resolve(), args.source_dir, args.proxy, args.official_ywh, args.cache_dir)
    print(json.dumps(result['platforms'], ensure_ascii=False, indent=2))
