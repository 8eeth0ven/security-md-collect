"""Traverse public AppChina search and publisher pages using their actual next links.

Store identity and publisher matching are discovery evidence, never SRC scope.
No page-number guessing, hidden credentials, binary downloads or access bypass.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import threading
import time
from urllib.parse import quote, unquote, urljoin, urlsplit

import requests

HOST = 'https://www.appchina.com'
PACKAGE = re.compile(r'[A-Za-z]\w*(?:\.[A-Za-z]\w*)+')
LOCAL = threading.local()
LOCK = threading.Lock()
RATE_LOCK = threading.Lock()
NEXT_REQUEST = 0.0
MIN_INTERVAL = 1.0
COOLDOWN_UNTIL = 0.0
RATE_LIMITED = threading.Event()


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    temporary.replace(path)


def get(url, cache):
    cache.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(url.encode()).hexdigest()
    meta_path, body_path = cache/(key+'.json'), cache/(key+'.body')
    if meta_path.exists() and body_path.exists():
        meta = json.loads(meta_path.read_text(encoding='utf-8'))
        if meta.get('http_status') == 200:
            return {**meta,'cache_hit':True,'network_attempted':False}, body_path.read_bytes()
    if RATE_LIMITED.is_set():
        return {'url':url,'http_status':0,'observed_at':now(),
                'network_attempted':False,'error':'global_rate_limit_circuit_open'},b''
    if not hasattr(LOCAL, 'session'):
        LOCAL.session = requests.Session()
        LOCAL.session.trust_env = False
    data = b''
    for attempt in range(2):
        global NEXT_REQUEST, COOLDOWN_UNTIL
        with RATE_LOCK:
            if RATE_LIMITED.is_set():
                return {'url':url,'http_status':0,'observed_at':now(),
                        'network_attempted':False,'error':'global_rate_limit_circuit_open'},b''
            wait = max(NEXT_REQUEST, COOLDOWN_UNTIL) - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            NEXT_REQUEST = time.monotonic() + MIN_INTERVAL
        try:
            response = LOCAL.session.get(url, timeout=14, headers={'User-Agent':'Mozilla/5.0'})
            data = response.content
            meta = {'url':url, 'final_url':response.url, 'http_status':response.status_code,
                    'network_attempted':True,
                    'observed_at':now(), 'sha256':hashlib.sha256(data).hexdigest(),
                    'bytes':len(data), 'content_type':response.headers.get('Content-Type','')}
            if response.status_code == 429:
                # Shared backoff, never six simultaneous retries against a limit.
                retry = response.headers.get('Retry-After', '60')
                cooldown = float(retry) if retry.isdigit() else 60.0
                with RATE_LOCK:
                    COOLDOWN_UNTIL = max(COOLDOWN_UNTIL, time.monotonic()+max(60,cooldown))
                meta['retry_after_seconds'] = max(60,cooldown)
                RATE_LIMITED.set()
                break
            if response.status_code not in (429, 500, 502, 503, 504):
                break
        except requests.RequestException as error:
            meta = {'url':url, 'http_status':0, 'observed_at':now(), 'error':type(error).__name__}
        time.sleep(.4 * (attempt+1))
    with LOCK:
        with (cache/'request-history.jsonl').open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(meta,ensure_ascii=False)+'\n')
        body_path.write_bytes(data)
        atomic_json(meta_path, meta)
    return meta, data


def plain(value):
    return html.unescape(re.sub(r'<[^>]+>', '', value or '')).strip()


def listing(body, kind='search'):
    text = body.decode('utf-8', errors='replace')
    if kind == 'search':
        match = re.search(r'<ul class="app-list">(.*?)</ul>', text, re.S)
        recognized = match is not None or 'class="search-empty"' in text or '没有找到' in text
        region = match.group(1) if match else ''
        entries = re.findall(r'<li class="has-border app">(.*?)</li>', region, re.S)
    else:
        match = re.search(r'<div class="developer-app-list">(.*?)<!-- pagination', text, re.S)
        recognized = match is not None
        region = match.group(1) if match else ''
        entries = re.findall(r'<li class="appInfo">(.*?)</li>', region, re.S)
    rows = {}
    for entry in entries:
        link = re.search(r'href="(/app/[^"?#]+)"', entry)
        if not link:
            continue
        package = unquote(link.group(1).split('/app/',1)[1])
        if not PACKAGE.fullmatch(package):
            continue
        title = re.search(r'(?:class="app-name" title|class="name"[^>]*title)="([^"]+)"', entry)
        if not title:
            title = re.search(r'<img[^>]*alt="([^"]+)"', entry)
        rows[package] = {'package':package, 'name':plain(title.group(1)) if title else '',
                         'detail_url':urljoin(HOST,link.group(1))}
    next_match = re.search(r'<a[^>]*class="next"[^>]*href="([^"]+)"',text)
    next_url = urljoin(HOST,html.unescape(next_match.group(1))) if next_match else ''
    # Only follow same-origin, same-family links actually supplied by the page.
    family = '/sou/' if kind == 'search' else '/developer/info/'
    if next_url and (urlsplit(next_url).hostname != 'www.appchina.com' or not urlsplit(next_url).path.startswith(family)):
        raise ValueError('Unexpected next link')
    return {'recognized':recognized, 'rows':list(rows.values()), 'next_url':next_url}


def detail(body, package):
    text = body.decode('utf-8', errors='replace')
    title = re.search(r'<h1 class="app-name">(.*?)</h1>', text, re.S)
    developer = re.search(r'<a[^>]*href="(/developer/info/packageName/'+re.escape(package)+r')"[^>]*>(.*?)</a>',text,re.S)
    if not title or not developer or not re.search(r'格式[：:]\s*(?:apk|APK)', text):
        return None
    version = re.search(r'版本[：:]([^<]+)',text)
    updated = re.search(r'更新[：:]([^<]+)',text)
    return {'name':plain(title.group(1)), 'package':package, 'developer':plain(developer.group(2)),
            'developer_url':urljoin(HOST,developer.group(1)),
            'version':plain(version.group(1)) if version else '',
            'store_updated_at':plain(updated.group(1)) if updated else ''}


def publisher_match(publisher, aliases):
    """Latin aliases use word boundaries, so ARM cannot match Carman."""
    publisher = str(publisher or '').casefold()
    for alias in aliases:
        alias = str(alias or '').strip().casefold()
        if not alias:
            continue
        if re.fullmatch(r'[a-z0-9 .&/-]+', alias):
            if re.search(r'(?<![a-z0-9])'+re.escape(alias)+r'(?![a-z0-9])',publisher):
                return True
        elif alias in publisher:
            return True
    return False


def traverse(url, cache, kind, label, checkpoint):
    visited, fingerprints, rows, pages = set(), set(), {}, []
    next_url = url
    state, reason = 'exhausted', 'no_next_link'
    while next_url:
        if next_url in visited:
            state,reason='repeated','next_link_cycle'
            break
        visited.add(next_url)
        meta,body=get(next_url,cache)
        if meta.get('http_status')!=200:
            pages.append({**meta,'page':len(pages)+1,'raw_rows':0,'new_packages':0,'has_next':None})
            state,reason=('rate_limited','shared_rate_limit_circuit') if meta.get('http_status')==429 or meta.get('error')=='global_rate_limit_circuit_open' else ('blocked','http_or_transport_failure')
            break
        parsed=listing(body,kind)
        packages=sorted(r['package'] for r in parsed['rows'])
        signature=hashlib.sha256('\n'.join(packages).encode()).hexdigest()
        new=[r for r in parsed['rows'] if r['package'] not in rows]
        pages.append({**meta,'page':len(pages)+1,'raw_rows':len(parsed['rows']),
                      'new_packages':len(new),'has_next':bool(parsed['next_url']),
                      'next_url':parsed['next_url'],'package_set_sha256':signature})
        if not parsed['recognized']:
            state,reason='blocked','unrecognized_listing_or_redirect'
            break
        if packages and signature in fingerprints:
            state,reason='repeated','repeated_package_set'
            break
        fingerprints.add(signature)
        for r in parsed['rows']:
            rows.setdefault(r['package'],dict(r,listing_source=next_url))
        next_url=parsed['next_url']
        if next_url and not parsed['rows']:
            state,reason='blocked','empty_page_with_next_link'
            break
        time.sleep(.08)
    result={'source':'AppChina','kind':kind,'label':label,'start_url':url,
            'status':state,'termination_reason':reason,'pages_checked':len(pages),
            'resume_url':next_url if state!='exhausted' else '',
            'unique_packages':len(rows),'pages':pages,'rows':list(rows.values()),'checked_at':now()}
    atomic_json(checkpoint,result)
    return result


def discover(base, cache, workers=6, publishers_only=False):
    from discover_vendor_apps import ALIASES, QUERIES
    base,cache=Path(base),Path(cache)
    workers=max(1,min(int(workers),6))
    vendors=json.loads((base/'资产/vendors.json').read_text(encoding='utf-8'))
    previous=json.loads((base/'赏金APK/vendor-app-discovery.json').read_text(encoding='utf-8'))
    checkpoint=cache/'queries';checkpoint.mkdir(parents=True,exist_ok=True)
    plans={}
    for vendor in vendors:
        name=vendor['vendor'];query=QUERIES.get(name,name.split('（')[0].split('(')[0].strip())
        queries=[query]
        # Search distinct domestic product brands as well as parent-company names.
        if name in ALIASES:
            queries.extend(a for a in ALIASES[name] if re.search('[\u4e00-\u9fff]',a) and len(a)>1)
        for query in ([] if publishers_only else dict.fromkeys(queries)):
            plans.setdefault(query,[]).append(name)
    results=[]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(traverse,HOST+'/sou/'+quote(query,safe=''),cache/'http','search',query,
                             checkpoint/(hashlib.sha256(query.encode()).hexdigest()+'.json')):query for query in plans}
        for future in as_completed(futures):
            result=future.result();result['vendors']=plans[futures[future]];results.append(result)
            print(json.dumps({'query':result['label'],'status':result['status'],'pages':result['pages_checked'],'packages':result['unique_packages'],'queries_done':len(results),'queries_total':len(plans)},ensure_ascii=False),flush=True)
    associations={}
    for result in results:
        for row in result['rows']:
            for vendor in result['vendors']:
                associations.setdefault(row['package'],{}).setdefault(vendor,row['listing_source'])
    # Known Android packages seed exact publisher directories even if their
    # product brand is absent from a parent-company keyword search.
    for app in previous['apps']:
        associations.setdefault(app['package'],{}).setdefault(app['vendor'],app.get('package_source_url',''))
    if publishers_only:
        associations={}
    details={};failed_details=[]
    def one(package):
        url=HOST+'/app/'+quote(package,safe='.')
        meta,body=get(url,cache/'http')
        record=detail(body,package) if meta.get('http_status')==200 else None
        return package,record,meta
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for package,record,meta in pool.map(one,associations):
            if record:details[package]={**record,'metadata':meta}
            else:failed_details.append({'package':package,**meta,'status':'detail_unavailable_or_non_apk'})
    publisher_plans={}
    apps=[]
    known={(r['vendor'],r['package']):r for r in previous['apps']}
    vendor_map={v['vendor']:v for v in vendors}
    def aliases(vendor):
        return ALIASES.get(vendor,[vendor.split('（')[0].split('(')[0].split('/')[0].strip()])
    for package,record in details.items():
        for vendor,source in associations[package].items():
            # Prior reviewed seeds remain candidate associations, not ownership proof.
            if (vendor,package) not in known and not publisher_match(record['developer'],aliases(vendor)):
                continue
            publisher_plans.setdefault(record['developer_url'],{'developer':record['developer'],'vendors':set()})['vendors'].add(vendor)
            apps.append({'vendor':vendor,'name':record['name'],'package':package,'platform':'android',
                         'developer':record['developer'],'version':record['version'],
                         'discovery_source':'应用汇','discovery_source_url':source or record['metadata']['url'],
                         'package_source_url':record['metadata']['url'],'download_page':record['metadata']['url'],
                         'download_state':'store_page_verified','scope_status':'unverified',
                         'ownership_status':'publisher_name_match_needs_review',
                         'observed_at':record['metadata']['observed_at'],'source_sha256':record['metadata']['sha256'],
                         'detail_metadata':record['metadata'],'notes':'商店应用及开发者已读取；厂商归属、SRC范围与奖金需独立核查。'})
    if publishers_only:
        # An observed publisher name groups seeds, but one seed URL still has to
        # return a real developer listing before any next link is followed.
        groups={}
        for app in previous['apps']:
            if not app.get('developer'):
                continue
            group=groups.setdefault(app['developer'],{'package':app['package'],'vendors':set()})
            group['vendors'].add(app['vendor'])
        publisher_plans={HOST+'/developer/info/packageName/'+quote(group['package'],safe='.'):
                         {'developer':developer,'vendors':group['vendors']} for developer,group in groups.items()}
    publisher_results=[]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(traverse,url,cache/'http','publisher',plan['developer'],
                             checkpoint/(hashlib.sha256(url.encode()).hexdigest()+'.json')):url for url,plan in publisher_plans.items()}
        for future in as_completed(futures):
            result=future.result();result['vendors']=sorted(publisher_plans[futures[future]]['vendors']);publisher_results.append(result)
            print(json.dumps({'publisher':result['label'],'status':result['status'],'pages':result['pages_checked'],'packages':result['unique_packages'],'publishers_done':len(publisher_results),'publishers_total':len(publisher_plans)},ensure_ascii=False),flush=True)
    missing={r['package'] for result in publisher_results for r in result['rows']}-details.keys()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for package,record,meta in pool.map(one,missing):
            if record:details[package]={**record,'metadata':meta}
            else:failed_details.append({'package':package,**meta,'status':'detail_unavailable_or_non_apk'})
    for result in publisher_results:
        for row in result['rows']:
            record=details.get(row['package'])
            if not record or record['developer']!=result['label']:
                continue
            for vendor in result['vendors']:
                apps.append({'vendor':vendor,'name':record['name'],'package':record['package'],'platform':'android',
                             'developer':record['developer'],'version':record['version'],
                             'discovery_source':'应用汇开发者目录','discovery_source_url':row['listing_source'],
                             'package_source_url':record['metadata']['url'],'download_page':record['metadata']['url'],
                             'download_state':'store_page_verified','scope_status':'unverified',
                             'ownership_status':'exact_store_publisher_needs_group_review',
                             'observed_at':record['metadata']['observed_at'],'source_sha256':record['metadata']['sha256'],
                             'detail_metadata':record['metadata'],'notes':'开发者目录逐页遍历，详情开发者名称再次精确核对；集团归属和SRC范围独立待核。'})
    # Keep old confirmed scope evidence. Do not overwrite it with store discovery.
    merged={(r['vendor'],r['package']):r for r in previous['apps']}
    for app in apps:
        key=app['vendor'],app['package']
        old=merged.get(key)
        if old:
            old.setdefault('additional_identity_sources',[]).append({'url':app['package_source_url'],'source':'应用汇','observed_at':app['observed_at'],'sha256':app['source_sha256']})
        else:merged[key]=app
    all_checks=results+publisher_results
    public_checks=[{k:v for k,v in r.items() if k!='rows'} for r in all_checks]
    output={**previous,'generated_at':now(),'apps':sorted(merged.values(),key=lambda r:(r['vendor'],r['package'])),
            'pagination_checks':public_checks,'detail_failures':failed_details}
    output['summary']={**previous.get('summary',{}),'candidate_apps':len(merged),
        'appchina_new_associations':len(merged)-len(previous['apps']),
        'pagination_queries':len(all_checks),'pagination_pages':sum(r['pages_checked'] for r in all_checks),
        'pagination_exhausted':sum(r['status']=='exhausted' for r in all_checks),
        'pagination_blocked_or_repeated':sum(r['status']!='exhausted' for r in all_checks),
        'appchina_detail_verified':len(details),'appchina_detail_failures':len(failed_details)}
    output['limits']=[line for line in previous.get('limits',[]) if '只检索' not in line]
    output['limits'].extend(['应用汇仅按当前公开页面的真实next链接遍历；exhausted仅表示该查询/开发者列表已无next，不代表厂商全部应用。',
                             '发布者列表重复、HTTP失败、未识别页面均保留非完成状态，不能计作末页。',
                             '应用宝SearchList当前组件没有应用级分页；布局offset是卡片分页，不冒称已翻完厂商所有应用。'])
    atomic_json(cache/'all-listing-rows.json',all_checks)
    atomic_json(cache/'verified-details.json',details)
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--cache-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--workers',type=int,default=6)
    parser.add_argument('--publishers-only',action='store_true',help='Prioritize exact known publisher directories instead of broad keyword searches')
    args=parser.parse_args()
    result=discover(args.base.resolve(),args.cache_dir.resolve(),args.workers,args.publishers_only)
    atomic_json(args.output,result)
    print(json.dumps(result['summary'],ensure_ascii=False),flush=True)
