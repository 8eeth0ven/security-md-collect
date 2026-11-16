"""Follow Baidu Mobile Assistant's observed pn/hasNextPage search contract.

The frontend calls /api/appsearch and sets noMore only for hasNextPage=false.
Search rows are identifiers; Android package/developer identity comes from the
matching appDoc in each public software detail page, not recommendations.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import re
import threading
from urllib.parse import quote

import market_pagination as market
from discover_vendor_apps import ALIASES, QUERIES

HOST='https://shouji.baidu.com'
LOCK=threading.Lock()


def parse_detail(body, docid):
    text=body.decode('utf-8',errors='replace')
    if 'window.__INITIAL_STATE__=' not in text:
        return None
    try:
        state,_=json.JSONDecoder().raw_decode(text.split('window.__INITIAL_STATE__=',1)[1])
        entries=state['appDoc']['resList']
        # The store keeps historical docid URLs and resolves them to its current
        # appDoc. Anchor to the requested resList key, never a recommendation.
        for key,item in entries.items():
            if key!='d_'+str(docid)+'.html':
                continue
            record=item.get('data',{}).get('appDocNew',{}).get('appDoc',{})
            if market.PACKAGE.fullmatch(str(record.get('package',''))) and record.get('developername'):
                return {'package':record['package'],'name':record.get('sname',''),
                        'developer':record['developername'],'version':record.get('versionname',''),
                        'docid':record.get('docid'),'requested_docid':docid,
                        'store_updated_at':record.get('updatetime',''),
                        'store_category':record.get('catename','')}
    except (ValueError,KeyError,TypeError):
        pass
    return None


def search_pages(query, cache):
    pn=0;pages=[];rows={};fingerprints=set();status='exhausted';reason='has_next_page_false'
    while True:
        url=HOST+'/api/appsearch?word='+quote(query,safe='')+'&pn='+str(pn)
        meta,body=market.get(url,cache)
        if meta.get('http_status')!=200:
            pages.append({**meta,'pn_requested':pn,'raw_rows':0,'new_docids':0})
            status='rate_limited' if meta.get('http_status')==429 or meta.get('error')=='global_rate_limit_circuit_open' else 'blocked'
            reason='http_or_transport_failure';break
        try:
            response=json.loads(body)
            data=response['data'];actual_pn=int(data['pn']);has_next=data['hasNextPage']
            # The observed terminal response can omit data[] entirely while
            # explicitly returning hasNextPage=false (e.g. 小红书 pn=4).
            items=data.get('data',[]) if has_next is False else data['data']
            if response.get('errorCode')!=0 or not isinstance(items,list) or type(has_next) is not bool:
                raise ValueError('Unrecognized response')
        except (ValueError,KeyError,TypeError):
            pages.append({**meta,'pn_requested':pn,'raw_rows':0,'new_docids':0})
            status,reason='blocked','unrecognized_search_response';break
        ids=[str(r.get('docid')) for r in items if r.get('docid') is not None]
        signature=hashlib.sha256('\n'.join(sorted(ids)).encode()).hexdigest()
        pages.append({**meta,'pn_requested':pn,'pn_returned':actual_pn,'has_next_page':has_next,
                      'reported_total':data.get('total'),'raw_rows':len(items),
                      'new_docids':sum(i not in rows for i in ids),'docid_set_sha256':signature})
        if actual_pn!=pn:
            status,reason='repeated','pn_not_advanced';break
        if ids and signature in fingerprints:
            status,reason='repeated','repeated_result_set';break
        fingerprints.add(signature)
        for row in items:
            if row.get('docid') is not None:
                rows.setdefault(str(row['docid']),{**row,'listing_source':url})
        if not has_next:
            break
        if not ids:
            status,reason='blocked','empty_page_claiming_next';break
        pn+=1
    return {'source':'百度手机助手','kind':'keyword_search','query':query,'start_url':HOST+'/search?word='+quote(query,safe=''),
            'status':status,'termination_reason':reason,'pages_checked':len(pages),
            'resume_pn':pn if status!='exhausted' else None,
            'successful_pages':sum(p.get('http_status')==200 for p in pages),
            'unique_docids':len(rows),'pages':pages,'rows':list(rows.values()),'checked_at':market.now()}


def discover(base, cache, output, workers=4):
    base,cache,output=Path(base),Path(cache),Path(output)
    cache.mkdir(parents=True,exist_ok=True)
    market.MIN_INTERVAL=.5
    vendors=json.loads((base/'资产/vendors.json').read_text(encoding='utf-8'))
    previous=json.loads((base/'赏金APK/vendor-app-discovery.json').read_text(encoding='utf-8'))
    known={(r['vendor'],r['package']):r for r in previous['apps']}
    publisher_vendors={}
    for r in previous['apps']:
        publisher_vendors.setdefault(r.get('developer',''),set()).add(r['vendor'])
    priority=['美团','网易','京东','小红书','金山办公','百度','字节跳动','华为','荣耀','vivo','小米','腾讯','东方财富','快手','蚂蚁集团','阿里巴巴']
    vendors.sort(key=lambda v:(priority.index(v['vendor']) if v['vendor'] in priority else len(priority),v['vendor']))
    checks=[];apps={};detail_failures=[]
    total_queries=len(vendors)
    def write_partial():
        result={'generated_at':market.now(),'apps':sorted(apps.values(),key=lambda r:(r['vendor'],r['package'])),
                'pagination_checks':checks,'detail_failures':detail_failures,
                'summary':{'planned_vendor_queries':total_queries,'vendor_queries_finished':len(checks),
                           'successful_pages':sum(r['successful_pages'] for r in checks),
                           'exhausted_queries':sum(r['status']=='exhausted' for r in checks),
                           'new_apps':sum(k not in known for k in apps),'verified_associations':len(apps)},
                'limits':['hasNextPage=false仅证明该关键词结果走到接口末页，不代表厂商全部应用。',
                          '搜索匹配/商店开发者名称不自动证明集团归属或SRC范围；所有新增记录等待官方范围核查。',
                          '包名和开发者从软件详情主appDoc获取，排除推荐卡；没有下载或校验APK二进制。']}
        market.atomic_json(output,result)
    def one(vendor):
        name=vendor['vendor'];query=QUERIES.get(name,name.split('（')[0].split('(')[0].strip())
        if name=='金山办公':query='WPS'
        result=search_pages(query,cache/'http');result['vendor']=name
        found=[];failed=[]
        aliases=ALIASES.get(name,[name.split('（')[0].split('(')[0].split('/')[0].strip()])
        for row in result['rows']:
            docid=row['docid'];url=HOST+'/software/'+str(docid)+'.html'
            meta,body=market.get(url,cache/'http')
            detail=parse_detail(body,docid) if meta.get('http_status')==200 else None
            if not detail:
                failed.append({'vendor':name,'docid':docid,**meta,'status':'detail_identity_unavailable'})
                continue
            developer=detail['developer'];package=detail['package']
            if not market.publisher_match(developer,aliases) and name not in publisher_vendors.get(developer,set()) and (name,package) not in known:
                continue
            found.append({'vendor':name,'name':detail['name'],'package':package,'platform':'android',
                          'developer':developer,'version':detail['version'],'discovery_source':'百度手机助手分页搜索',
                          'discovery_source_url':row['listing_source'],'package_source_url':url,'download_page':url,
                          'download_state':'store_page_verified','scope_status':'unverified',
                          'ownership_status':'publisher_name_match_needs_review','observed_at':meta['observed_at'],
                          'source_sha256':meta.get('sha256'),'detail_metadata':meta,
                          'notes':'百度手机助手真实pn分页结果；详情主appDoc核对Android包名和开发者，集团归属及SRC范围另核。'})
        result.pop('rows',None)
        return result,found,failed
    with ThreadPoolExecutor(max_workers=max(1,min(workers,6))) as pool:
        futures=[pool.submit(one,v) for v in vendors]
        for future in as_completed(futures):
            result,found,failed=future.result()
            with LOCK:
                checks.append(result);detail_failures.extend(failed)
                for app in found:apps[app['vendor'],app['package']]=app
                write_partial()
            print(json.dumps({'vendor':result['vendor'],'status':result['status'],'pages':result['successful_pages'],
                              'verified':len(found),'finished':len(checks),'planned':total_queries},ensure_ascii=False),flush=True)
    return json.loads(output.read_text(encoding='utf-8'))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--cache-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--workers',type=int,default=4)
    args=parser.parse_args()
    result=discover(args.base.resolve(),args.cache_dir.resolve(),args.output.resolve(),args.workers)
    print(json.dumps(result['summary'],ensure_ascii=False),flush=True)
