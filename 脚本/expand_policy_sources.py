"""Discover explicit GitHub scope repositories and account default policies.

Uses the collector's exclusive lock and state writer. Never treats all repositories
under an account as bounty scope; this is only public document discovery.
"""
import argparse
import json
import re
import time
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit

import collect


def github_seed(value):
    try:
        parsed = urlsplit(str(value or '').strip())
    except ValueError:
        return None
    if parsed.scheme not in ('http', 'https') or parsed.hostname != 'github.com':
        return None
    parts = parsed.path.strip('/').split('/')
    if not parts or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,38}', parts[0]):
        return None
    if parts[0].lower() in ('orgs', 'users', 'features', 'settings', 'login', 'topics', 'search'):
        return None
    repo = parts[1].removesuffix('.git') if len(parts) > 1 else ''
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', repo) or repo in ('.', '..'):
        repo = None
    return parts[0], repo


def seeds(source_dir, owners):
    found = []
    for name in ('hackerone', 'bugcrowd', 'intigriti', 'yeswehack'):
        for program in json.loads((source_dir / (name+'.json')).read_text(encoding='utf-8')):
            for target in program['targets']['in_scope']:
                value = target.get('asset_identifier') or target.get('endpoint') or target.get('uri') or target.get('target')
                parsed = github_seed(value)
                if parsed:
                    owner, repo = parsed
                    found.append({'owner': owner, 'repo': repo, 'vendor': owners.get(owner.casefold()) or program['name'],
                                  'program_url': program.get('url') or ('https://yeswehack.com/programs/'+str(program.get('id', ''))),
                                  'scope_value': value, 'platform': name})
    return found


def run(source_dir, budget):
    if not collect.acquire_lock():
        raise RuntimeError('Collector is active; retry after it releases its lock')
    try:
        state = collect.load_state()
        vendors, owner_map = collect.merge_vendors()
        owners = {owner.casefold(): vendor for owner, vendor in owner_map.items()}
        discovered = seeds(source_dir, owners)
        mapping = defaultdict(set)
        for seed in discovered:
            if seed['owner'].casefold() not in owners:
                mapping[seed['vendor']].add(seed['owner'])
        mapping_file = collect.ASSETS / '厂商映射-范围补充.json'
        old_mapping = json.loads(mapping_file.read_text(encoding='utf-8')) if mapping_file.exists() else []
        additions = [{'vendor': vendor, 'src': '公开平台范围（仅用于策略发现）', 'orgs': sorted(orgs),
                      'note': '组织在公开范围中出现，不代表其所有仓库均可测试；见 索引/policy-discovery.json。'}
                     for vendor, orgs in sorted(mapping.items())]
        mapping_file.write_text(json.dumps(old_mapping+additions, ensure_ascii=False, indent=1), encoding='utf-8')
        vendors, owner_map = collect.merge_vendors()
        owner_case = {owner.casefold(): owner for owner in owner_map}
        tasks = defaultdict(dict)
        for owner in owner_map:
            full = owner+'/.github'
            if collect.probe_due(state, full):
                tasks[owner][full] = {}
        for seed in discovered:
            owner = owner_case[seed['owner'].casefold()]
            if seed['repo']:
                full = owner+'/'+seed['repo']
                if collect.probe_due(state, full):
                    tasks[owner][full] = {}
        before = len(state['repos_data'])
        deadline = time.time()+budget
        for owner, repos in tasks.items():
            cached = collect.load_meta_cache(owner)
            cached.update(repos)
            collect.save_meta_cache(owner, cached)
        all_repos = {full: meta for repos in tasks.values() for full, meta in repos.items()}
        collect.probe_and_record(state, 'scope-seeds', '', all_repos, deadline, owner_vendors=owner_map)
        pending = sorted(full for repos in tasks.values() for full in repos if collect.probe_due(state, full))
        defaults = [{'owner': owner, 'policy_repo': owner+'/.github',
                     'path': state['repos_data'][owner+'/.github']['sec_path']}
                    for owner in owner_map if owner+'/.github' in state['repos_data']]
        report = {'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'), 'new_mapping_entries': additions,
                  'source_revision': json.loads((source_dir/'revision.json').read_text(encoding='utf-8')),
                  'scope_seeds': discovered, 'default_policy_repositories': defaults, 'pending': pending,
                  'added_policies': len(state['repos_data'])-before,
                  'limits': 'Account defaults are separate documents; inheritance is not expanded into per-repo counts.'}
        (collect.INDEX/'policy-discovery.json').write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
        collect.save_state(state)
        collect.write_outputs(state, 'html')
        return {key:len(value) if isinstance(value, list) else value for key,value in report.items() if key != 'source_revision'}
    finally:
        collect.release_lock()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', required=True, type=Path)
    parser.add_argument('--budget', type=int, default=900)
    args = parser.parse_args()
    print(json.dumps(run(args.source_dir, args.budget), ensure_ascii=False))
