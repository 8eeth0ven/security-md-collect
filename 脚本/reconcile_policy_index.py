"""Reconcile public policy snapshots without creating private collector state.

GitHub repository identifiers are case-insensitive. Prefer the mapped vendor and
latest actual verification, preserve earliest first_seen, and keep original files.
Cross-vendor ambiguity is reported rather than silently reassigned.
"""
import argparse
import csv
import json
import time
from collections import defaultdict
from pathlib import Path

from audit_priority_projects import atomic_json


def reconcile(base):
    base = Path(base).resolve()
    vendors = json.loads((base/'资产/vendors.json').read_text(encoding='utf-8'))
    mapped = {}
    for vendor in vendors:
        for owner in vendor['orgs']:
            mapped.setdefault(owner.casefold(), vendor['vendor'])
    files = sorted((base/'厂商').glob('*/repos.json'))
    original = {file: json.loads(file.read_text(encoding='utf-8')) for file in files}
    grouped = defaultdict(list)
    for file, rows in original.items():
        for row in rows:
            if row.get('sec_path') and row['sec_path'] != 'error':
                grouped[row['full_name'].casefold()].append((file, row))
    removed, replacements, decisions, ambiguous = set(), {}, [], []
    for identity, candidates in grouped.items():
        if len(candidates) < 2:
            continue
        canonical_vendor = mapped.get(identity.split('/')[0])
        owned = [(file,row) for file,row in candidates if row.get('vendor') == canonical_vendor]
        if not owned and len({row.get('vendor') for _,row in candidates}) > 1:
            ambiguous.append({'repository':identity,'vendors':sorted({row.get('vendor','') for _,row in candidates})})
            continue
        chosen_file, chosen = max(owned or candidates, key=lambda item: (item[1].get('last_verified') or '',item[1].get('first_seen') or ''))
        merged = dict(chosen)
        for _, row in candidates:
            for key, value in row.items():
                if not merged.get(key) and value is not None:
                    merged[key] = value
        first_seen = [row['first_seen'] for _,row in candidates if row.get('first_seen')]
        if first_seen:
            merged['first_seen'] = min(first_seen)
        for file,row in candidates:
            removed.add((file,row['full_name']))
        replacements[(chosen_file,chosen['full_name'])] = merged
        decisions.append({'repository':identity,'kept_full_name':merged['full_name'],
                          'vendor':merged.get('vendor'),'records_before':len(candidates),
                          'records_removed':len(candidates)-1,'first_seen':merged.get('first_seen'),
                          'last_verified':merged.get('last_verified'),'original_documents_preserved':True})
    all_rows, changed = [], []
    vendor_files = {}
    for file, records in original.items():
        revised=[]
        for row in records:
            key=(file,row['full_name'])
            if key in replacements:
                revised.append(replacements.pop(key))
            elif key not in removed:
                revised.append(row)
        if revised != records:
            revised.sort(key=lambda row:(-(row.get('stars') or 0),row['full_name'].casefold()))
            atomic_json(file,revised);changed.append(file.parent.name)
        all_rows.extend(row for row in revised if row.get('sec_path') and row['sec_path']!='error')
        vendor_files[file.parent.name]=revised
    # Refresh human manifests against the same de-duplicated records.
    from collect import safe_name
    for vendor in vendors:
        folder=base/'厂商'/safe_name(vendor['vendor'])
        rows=vendor_files.get(folder.name,[])
        if not folder.exists():
            folder.mkdir(parents=True)
            atomic_json(folder/'repos.json',rows)
        if folder.name not in changed and (folder/'清单.md').exists():
            continue
        lines=['# %s（%s）— 开源项目 SECURITY.MD 清单'%(vendor['vendor'],vendor.get('src') or '未知SRC'),'',
               '- 收录仓库数：**%d**（均含 SECURITY.md，原文在 %s/ 下按仓库存放）'%(len(rows),safe_name(vendor['vendor'])),
               '- GitHub 组织：'+'、'.join(vendor['orgs']),'- 更新时间：'+time.strftime('%Y-%m-%d %H:%M:%S'),'',
               '| 仓库（GitHub 项目页） | 星数 | 语言 | SECURITY.md（本地文本） | 项目链接 |','|---|---:|---|---|---|']
        for row in rows:
            lines.append('| %s | %s | %s | %s | %s |'%(row['full_name'],row.get('stars') if row.get('stars') is not None else '-',row.get('language') or '-',row.get('sec_path'),row.get('url') or 'https://github.com/'+row['full_name']))
        (folder/'清单.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    per_vendor=defaultdict(list)
    for row in all_rows:
        per_vendor[row.get('vendor') or row['org']].append(row)
    stats_path=base/'索引/统计.json'
    stats=json.loads(stats_path.read_text(encoding='utf-8'))
    stats['generated_at']=time.strftime('%Y-%m-%d %H:%M:%S')
    stats['mode']='priority-audit'
    stats['totals'].update(vendors=len(vendors),orgs=len(mapped),sec_repos=len(grouped))
    stats['negative_cache_status']='Historical summary from original collector; no negative cache reconstructed locally.'
    stats['vendors']=[{'vendor':v['vendor'],'src':v.get('src',''),'orgs':v['orgs'],'sec_repos':len(per_vendor[v['vendor']])} for v in vendors]
    atomic_json(stats_path,stats)
    with (base/'索引/总表.csv').open('w',newline='',encoding='utf-8-sig') as stream:
        writer=csv.writer(stream);writer.writerow(['厂商','SRC','组织','仓库','链接','星数','语言','SECURITY.md','描述'])
        for vendor in vendors:
            for row in sorted(per_vendor[vendor['vendor']],key=lambda r:(-(r.get('stars') or 0),r['full_name'].casefold())):
                writer.writerow([vendor['vendor'],vendor.get('src',''),row['org'],row['full_name'],row.get('url') or 'https://github.com/'+row['full_name'],row.get('stars',''),row.get('language',''),row['sec_path'],row.get('description','')])
    previous_path=base/'索引/政策索引整理.json'
    previous=json.loads(previous_path.read_text(encoding='utf-8')) if previous_path.exists() else {}
    previous_decisions={row['repository']:row for row in previous.get('deduplication',[])}
    previous_decisions.update({row['repository']:row for row in decisions})
    report={**previous,'generated_at':time.strftime('%Y-%m-%d %H:%M:%S'),
            'raw_records_before_this_pass':sum(len(rows) for rows in original.values()),
            'records_after':len(all_rows),'unique_repositories_after':len({row['full_name'].casefold() for row in all_rows}),
            'removed_duplicates_this_pass':sum(row['records_removed'] for row in decisions),
            'recorded_removed_duplicates':sum(row['records_removed'] for row in previous_decisions.values()),
            'deduplication':list(previous_decisions.values()),'ambiguous_vendor_ownership':ambiguous,
            'original_policy_documents_deleted':0}
    atomic_json(previous_path,report)
    print(json.dumps({k:v for k,v in report.items() if k!='deduplication'},ensure_ascii=False))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,default=Path(__file__).resolve().parents[1])
    reconcile(parser.parse_args().base)
