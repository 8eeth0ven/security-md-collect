"""Search actual known publisher names on MyApp and recheck Android details.

MyApp's current SearchList exposes one response rather than app pagination.
An exact developer query is an additional discovery path, not a full directory.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import threading
from urllib.parse import quote

from discover_vendor_apps import get, search_rows, detail_row, now
from market_pagination import atomic_json


def discover(base,cache,workers=4):
    base,cache=Path(base),Path(cache)
    cache.mkdir(parents=True,exist_ok=True)
    previous=json.loads((base/'赏金APK/vendor-app-discovery.json').read_text(encoding='utf-8'))
    groups={}
    for app in previous['apps']:
        if app.get('developer'):
            groups.setdefault(app['developer'],set()).add(app['vendor'])
    stop=threading.Event()
    def one(developer):
        url='https://sj.qq.com/search?q='+quote(developer,safe='')
        if stop.is_set():
            return developer,{'url':url,'http_status':0,'error':'rate_limit_circuit_open','network_attempted':False},[]
        meta,body=get(url,cache)
        if meta.get('http_status')==429:
            stop.set()
        raw=search_rows(body) if meta.get('http_status')==200 else []
        rows=[r for r in raw if developer in (r.get('developer'),r.get('operator'))]
        return developer,{**meta,'kind':'publisher_name_search','developer':developer,
                          'vendors':sorted(groups[developer]),'raw_android_rows':len(raw),
                          'exact_developer_rows':len(rows),'pagination_status':'non_paginated'},rows
    checks=[];candidates={}
    with ThreadPoolExecutor(max_workers=max(1,min(workers,6))) as pool:
        for developer,meta,rows in pool.map(one,groups):
            checks.append(meta)
            for row in rows:
                for vendor in groups[developer]:
                    candidates[vendor,row['pkg_name']]=(row,meta)
    def verify(item):
        (vendor,package),(row,source)=item
        url='https://sj.qq.com/appdetail/'+package
        if stop.is_set():
            return None
        meta,body=get(url,cache)
        if meta.get('http_status')==429:
            stop.set();return None
        found=detail_row(body,package) if meta.get('http_status')==200 else None
        if not found or source['developer'] not in (found.get('developer'),found.get('operator')):
            return None
        return {'vendor':vendor,'name':found['name'],'package':package,'platform':'android',
                'developer':found.get('developer') or found.get('operator'),'version':found.get('version_name',''),
                'discovery_source':'应用宝开发者全称搜索','discovery_source_url':source['url'],
                'package_source_url':url,'download_page':url,'download_state':'store_page_verified',
                'scope_status':'unverified','ownership_status':'exact_store_publisher_needs_group_review',
                'observed_at':meta['observed_at'],'source_sha256':meta.get('sha256'),'detail_metadata':meta,
                'notes':'开发者全称检索后，详情开发者再次精确对应；不是完整开发者目录，集团归属与SRC范围独立核查。'}
    with ThreadPoolExecutor(max_workers=max(1,min(workers,6))) as pool:
        apps=[row for row in pool.map(verify,candidates.items()) if row]
    known={(r['vendor'],r['package']) for r in previous['apps']}
    return {'generated_at':now(),'apps':apps,'new_apps':[r for r in apps if (r['vendor'],r['package']) not in known],
            'pagination_checks':checks,
            'summary':{'publisher_queries':len(checks),'verified_associations':len(apps),
                       'new_apps':sum((r['vendor'],r['package']) not in known for r in apps),
                       'failed_queries':sum(r.get('http_status')!=200 for r in checks)},
            'limits':['应用宝当前SearchList不暴露应用分页；以实际已知开发者全称检索，不冒充完整开发者目录。',
                      '同一商店开发者名称不是集团归属或SRC资格证明；需独立范围核查。']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--cache-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--workers',type=int,default=4)
    args=parser.parse_args()
    result=discover(args.base.resolve(),args.cache_dir.resolve(),args.workers)
    atomic_json(args.output,result)
    print(json.dumps(result['summary'],ensure_ascii=False))
