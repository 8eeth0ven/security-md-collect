"""Merge evidenced app reviews and confirmed proposals without erasing history.

Inputs are explicit JSON manifests, not raw HTTP caches. Paused programs remain
in the catalog; app identity, scope, reward and submission state stay separate.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path

from build_apk_board import PACKAGE, safe_url, write


def load(path, default=None):
    return json.loads(Path(path).read_text(encoding='utf-8')) if Path(path).exists() else default


def identity(row):
    return (str(row.get('vendor') or ''), str(row.get('package') or ''))


def record_identity(row):
    return (str(row.get('vendor') or ''), str(row.get('package') or row.get('target') or ''))


def arrays(paths, field=None):
    result = []
    for path in paths:
        data = load(path)
        if field and isinstance(data, dict):
            data = data.get(field, [])
        if not isinstance(data, list) or any(not isinstance(row, dict) for row in data):
            raise ValueError('Expected an array of review records: '+str(path))
        result.extend(data)
    return result


def source_coverage(paths, stamp):
    checks = []
    for path in paths:
        data = load(path)
        rows = data if isinstance(data, list) else data.get('pagination_checks', [])
        for raw in rows:
            row = {k:v for k,v in raw.items() if k not in ('apps','body','headers','cookies')
                   and not (k == 'rows' and isinstance(v, list))}
            if not row.get('source'):
                host = safe_url(row.get('url'))
                row['source'] = '腾讯应用宝' if 'sj.qq.com' in host else row.get('vendor') or '官方公告目录'
            checks.append(row)
    summaries = []
    for source in sorted({row['source'] for row in checks}):
        rows = [r for r in checks if r['source']==source]
        pages = [p for row in rows for p in row.get('pages', [])]
        ok = [p for p in pages if p.get('http_status')==200]
        summaries.append({'source':source,'query_checks':len(rows),
            'exhausted_queries':sum(r.get('status')=='exhausted' or r.get('exhausted') is True for r in rows),
            'non_paginated_queries':sum(str(r.get('pagination_status','')).startswith('non_paginated') for r in rows),
            'successful_page_observations':len(ok),
            'unique_successful_page_urls':len({p.get('url') for p in ok if p.get('url')}),
            'rate_limited_queries':sum(r.get('status')=='rate_limited' for r in rows)})
    return {'schema_version':1,'generated_at':stamp,'sources':summaries,'checks':checks,
            'limits':['Page observations and queued checks are not physical HTTP request counts.',
                      'An exhausted visible search is not a complete vendor product inventory.',
                      'Source or rate-limit failures retain pending cursors instead of being marked exhausted.']}


def validate_proposal(row):
    if not row.get('vendor') or not row.get('target'):
        raise ValueError('Confirmed app proposals need vendor and product')
    if row.get('scope_status') not in ('in_scope','confirmed'):
        raise ValueError('Unresolved apps cannot enter a confirmed inventory')
    if not safe_url(row.get('scope_source')) or not row.get('scope_evidence'):
        raise ValueError('Confirmed scope needs an official source and recorded evidence')
    if not (safe_url(row.get('download_page')) or safe_url(row.get('apk_direct'))):
        raise ValueError('Android proposals need a source-backed app entry')
    package = str(row.get('package') or '')
    if package and (not PACKAGE.fullmatch(package) or not safe_url(row.get('package_source_url'))):
        raise ValueError('Package IDs need their own identity source')
    if not row.get('scope_observed_at'):
        raise ValueError('Scope observation time must remain explicit')


def merge_inventory(existing, proposals):
    records = {record_identity(row): row for row in existing}
    for row in proposals:
        validate_proposal(row)
        records[record_identity(row)] = {**row, 'scope_status':'in_scope', 'download_verified':False}
    # One product in one official submission channel is one record, even when
    # a subsidiary and its parent supplied separate discovery labels.
    canonical = {}
    for row in records.values():
        key = (row.get('package') or row['vendor']+'::'+row['target'],
               row.get('program_url') or row.get('scope_source'))
        if key not in canonical:
            canonical[key] = row
        else:
            kept = canonical[key]
            kept['vendor_aliases'] = sorted(set(kept.get('vendor_aliases', [])) |
                                           set(row.get('vendor_aliases', [])) | {row['vendor']})
    return sorted(canonical.values(), key=lambda row:(row['vendor'],row['target'],row.get('package') or ''))


def merge(base, baseline_path, review_paths, src_paths, official_paths, discovery_paths, stamp=None,
          src_baseline=None, discovery_baseline=None, official_baseline=None, coverage_paths=None):
    base = Path(base)
    out = base/'赏金APK'
    stamp = stamp or datetime.now(timezone.utc).isoformat(timespec='seconds')
    baseline = load(baseline_path)
    if not isinstance(baseline, list):
        raise ValueError('A frozen per-app baseline is required')
    baseline_keys = {identity(row) for row in baseline}
    if len(baseline_keys) != len(baseline):
        raise ValueError('Duplicate baseline app identities')
    previous = load(discovery_baseline or out/'vendor-app-discovery.json', {'vendors':[], 'apps':[]})
    reviews = {identity(row):row for row in arrays(review_paths)}
    if not baseline_keys <= reviews.keys():
        raise ValueError('The requested baseline still has unreviewed app identities')
    src_proposals = arrays(src_paths)
    official_proposals = arrays(official_paths)
    old_src = load(src_baseline or out/'src_android.json', [])
    old_official = load(official_baseline or out/'official_android.json', [])
    src = merge_inventory(old_src, src_proposals)
    official = merge_inventory(old_official, official_proposals)
    apps = {identity(row):row for row in previous.get('apps', [])}
    for path in discovery_paths:
        data = load(path)
        rows = data if isinstance(data, list) else data.get('apps', data.get('new_apps', []))
        for row in rows:
            package = str(row.get('package') or '')
            if not row.get('vendor') or not PACKAGE.fullmatch(package):
                raise ValueError('Invalid Android discovery identity')
            if not safe_url(row.get('package_source_url')):
                raise ValueError('Discoveries require an identity evidence URL')
            key = identity(row)
            apps[key] = {**apps.get(key, {}), **row}
    proposals = {identity(row):row for row in src+official if row.get('package')}
    official_keys = {identity(row) for row in official}
    for row in src+official:
        if row.get('package'):
            for alias in row.get('vendor_aliases', []):
                proposals.setdefault((alias, row['package']), row)
    excluded = {identity(row):row for row in previous.get('excluded_apps', [])}
    for key, review in reviews.items():
        if key not in apps:
            continue
        app = apps[key]
        app['reviewed_at'] = review.get('reviewed_at') or review.get('checked_at') or stamp
        app['review_status'] = review.get('review_status', 'scope_unresolved')
        app['notes'] = str(review.get('notes') or review.get('reason') or review.get('scope_evidence') or app.get('notes') or '')
        app['review_source'] = './scope-review.json'
        if review.get('scope_status') == 'out_of_scope' or app['review_status'] in ('officially_excluded','out_of_scope','confirmed_out_of_scope'):
            if key in proposals:
                raise ValueError('An explicit scope exclusion conflicts with a confirmed proposal')
            app['scope_status'] = 'out_of_scope'
            app['scope_source'] = review.get('official_scope_source') or review.get('official_scope') or review.get('official_scope_url') or app.get('scope_source')
        if app['review_status'] in ('ownership_mismatch','confirmed_wrong_vendor','vendor_name_collision'):
            app.update(scope_status='ownership_mismatch', ownership_status='rejected_vendor_association')
            excluded[key] = app
            apps.pop(key)
    for key, record in proposals.items():
        if key in excluded:
            raise ValueError('A rejected vendor attribution conflicts with a confirmed proposal')
        if key not in apps:
            if key != identity(record):
                continue  # Alias-only keys refer to the canonical catalog row.
            apps[key] = {'vendor':record['vendor'],'name':record['target'],'package':record['package'],
                         'platform':'android','package_source_url':record['package_source_url'],
                         'download_page':record.get('download_page'), 'developer':record.get('developer',''),
                         'detail_metadata':record.get('download_metadata'), 'download_state':record.get('download_state',''),
                         'discovery_source_url':record.get('package_source_url')}
        apps[key].update(scope_status='confirmed',scope_source=record['scope_source'],
                         scope_review_source=record.get('scope_review_source'),
                         scope_match_type=record.get('scope_match_type',''),
                         scope_observed_at=record['scope_observed_at'],
                         program_state=record.get('program_state','unknown'),
                         submission_state=record.get('submission_state','unknown'),
                         program_state_source=record.get('program_state_source',''),
                         catalog_platform='official' if identity(record) in official_keys else 'src',
                         vendor_aliases=record.get('vendor_aliases', []),
                         notes=record.get('scope_notes') or record.get('scope_evidence',''))
    baseline_rows = []
    for item in baseline:
        key = identity(item)
        row = {**reviews[key]}
        if key in proposals:
            record = proposals[key]
            paused = any(record.get(k) in ('paused','closed','disabled') for k in ('program_state','submission_state'))
            row['review_status'] = 'confirmed_paused' if paused else 'confirmed_scope'
            row['catalog_platform'] = 'official' if identity(record) in official_keys else 'src'
        baseline_rows.append(row)
    counts = dict(Counter(row.get('review_status','scope_unresolved') for row in baseline_rows))
    ledger = {'schema_version':1,'generated_at':stamp,'baseline_candidates':len(baseline),
              'reviewed_candidates':len(baseline_rows),'result_counts':counts,'rows':baseline_rows,
              'additional_reviews':[row for key,row in reviews.items() if key not in baseline_keys],
              'limits':['A review can confirm scope, reject an attribution, or document an unresolved source.',
                        'Paused programs remain indexed when identity and last applicable scope are evidenced.',
                        'Bounty and current submission eligibility are separate from inclusion.']}
    previous.update(generated_at=stamp,apps=sorted(apps.values(),key=lambda r:(r['vendor'],r.get('name',''),r['package'])),
                    excluded_apps=sorted(excluded.values(),key=lambda r:(r['vendor'],r['package'])),
                    baseline_review_summary={k:v for k,v in ledger.items() if k not in ('rows','additional_reviews')},
                    review_manifest='scope-review.json')
    if coverage_paths:
        coverage = source_coverage(coverage_paths, stamp)
        write(out/'app-source-coverage.json',json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
        previous['source_coverage_summary'] = coverage['sources']
    previous['limits'] = ['Market searches cover visible results for recorded queries, not every vendor product.', 'Baidu follows pn/hasNextPage to the observed end; QQ developer SearchList is non-paginated.', 'AppChina rate limiting leaves unfinished queries; all stop reasons are recorded.', 'Identity, official scope, rewards and current submissions are reviewed separately; paused programs remain indexed.']
    summary = previous.setdefault('summary', {})
    summary.update(candidate_apps=len(apps),scope_confirmed_apps=sum(r.get('scope_status')=='confirmed' for r in apps.values()),
                   scope_unverified_apps=sum(r.get('scope_status') not in ('confirmed','out_of_scope') for r in apps.values()),
                   scope_excluded_apps=sum(r.get('scope_status')=='out_of_scope' for r in apps.values()),
                   excluded_vendor_associations=len(excluded),original_candidates_reviewed=len(baseline_rows),
                   original_review_counts=counts,domestic_src_records=len(src),official_program_records=len(official))
    summary['detail_verified_apps'] = sum(row.get('download_state')=='store_page_verified' for row in apps.values())
    summary['vendors_with_candidates'] = len({row['vendor'] for row in apps.values()})
    paged = {row.get('vendor'):row for row in (coverage.get('checks', []) if coverage_paths else [])
             if row.get('source')=='百度手机助手' and row.get('status')=='exhausted'}
    for vendor in previous.get('vendors', []):
        vendor['candidate_count'] = sum(r['vendor']==vendor['vendor'] for r in apps.values())
        if vendor['vendor'] in paged:
            check = paged[vendor['vendor']]
            vendor.update(pagination_source=check['source'],pagination_status='exhausted',
                          pagination_pages=check.get('pages_checked'),search_url=check.get('start_url'),
                          checked_at=check.get('checked_at'),
                          status='android_candidates_found' if vendor['candidate_count'] else 'no_publisher_match_in_exhausted_search',
                          notes='已跟随该来源的真实pn与hasNextPage遍历到末页；这不等于厂商所有应用全集，范围与接收状态另核。')
    for name, data in [('src_android.json',src),('official_android.json',official),('scope-review.json',ledger),('vendor-app-discovery.json',previous)]:
        write(out/name,json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    snapshot = load(out/'snapshot.json', {})
    snapshot.update(generated_at=stamp,domestic_sources_at=stamp,app_reviews_at=stamp)
    write(out/'snapshot.json',json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n')
    backlog = load(out/'src-backlog.json', {})
    targets = {(row['vendor'],row['target']) for row in src}
    packages = {identity(row) for row in src if row.get('package')}
    backlog['pending_products'] = [row for row in backlog.get('pending_products', [])
        if identity(row) not in packages and (row.get('vendor'),row.get('product') or row.get('target')) not in targets]
    for vendor in backlog.get('vendor_registry', []):
        selected = [row for row in src if row['vendor'] == vendor['vendor'] or vendor['vendor'] in row.get('vendor_aliases', [])]
        vendor['confirmed_android_targets'] = len(selected)
        if selected:
            vendor.update(status='partial_product_inventory_confirmed', checked_at=stamp,
                          source_urls=sorted({row['scope_source'] for row in selected if row.get('scope_source')}),
                          paused_android_targets=sum(any(row.get(k) in ('paused','closed','disabled') for k in ('program_state','submission_state')) for row in selected),
                          note='已确认身份与现行或最后已知范围；暂停也保留，当前接收和奖励资格见逐条记录。')
    backlog.update(observed_at=stamp,confirmed_android_targets=len(src),original_candidate_review=summary['original_review_counts'])
    write(out/'src-backlog.json',json.dumps(backlog,ensure_ascii=False,indent=2)+'\n')
    # Keep the importer's evidence input in sync, so a later evidence import
    # cannot silently revert this round's confirmed additions.
    evidence = [row for row in load(out/'src-evidence.json', [])
        if row.get('scope_status') != 'confirmed' and identity(row) not in packages
        and (row.get('vendor'),row.get('product')) not in targets]
    for row in src:
        evidence.append({**row,'src_name':row.get('handle') or row['program'],
            'product':row['target'],'scope_status':'confirmed','scope_url':row['scope_source'],
            'observed_at':row['scope_observed_at'],'reward_status':row.get('bounty_type','unknown')})
    write(out/'src-evidence.json',json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
    return {'src':len(src),'official':len(official),'apps':len(apps),'excluded':len(excluded),
            'reviewed_baseline':len(baseline_rows),'baseline_results':counts}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--review',type=Path,action='append',default=[])
    parser.add_argument('--src-proposals',type=Path,action='append',default=[])
    parser.add_argument('--official-proposals',type=Path,action='append',default=[])
    parser.add_argument('--discovery',type=Path,action='append',default=[])
    parser.add_argument('--observed-at')
    parser.add_argument('--src-baseline',type=Path,help='Frozen pre-run inventory for reproducible review revisions')
    parser.add_argument('--official-baseline',type=Path)
    parser.add_argument('--discovery-baseline',type=Path)
    parser.add_argument('--coverage',type=Path,action='append',default=[])
    args = parser.parse_args()
    print(json.dumps(merge(args.base,args.baseline,args.review,args.src_proposals,args.official_proposals,args.discovery,args.observed_at,
                           args.src_baseline,args.discovery_baseline,args.official_baseline,args.coverage),ensure_ascii=False))
