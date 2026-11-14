"""Reconcile historical Android rows against complete public official scopes.

Only reads platform metadata. No target requests, APK downloads or credentials.
Cached responses belong outside the publishing checkout; publish the review manifest.
"""
import argparse
import fnmatch
import hashlib
import html
import json
import re
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from build_apk_board import PACKAGE, PLATFORMS, safe_url, write
from update_apk_sources import android_target, package_from

QUERY = '''query($handle:String!,$after:String,$archived:Boolean!){team(handle:$handle){
 name handle offers_bounties submission_state state
 structured_scopes(first:100,after:$after,archived:$archived){
 pageInfo{endCursor hasNextPage} nodes{asset_identifier asset_type eligible_for_bounty
 eligible_for_submission archived_at instruction}}}}'''
LOCAL = threading.local()


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def session():
    if not hasattr(LOCAL, 'session'):
        obj = requests.Session()
        retry = Retry(total=2, backoff_factor=.8, status_forcelist=[429,500,502,503,504],
                      allowed_methods=['GET','POST'], respect_retry_after_header=True)
        obj.mount('https://', HTTPAdapter(max_retries=retry))
        obj.headers['User-Agent'] = 'security-md-collect/public-scope-review'
        LOCAL.session = obj
    return LOCAL.session


def get(url):
    response = session().get(url, timeout=25)
    response.raise_for_status()
    return response


def canonical(value):
    value = str(value or '').strip()
    if value.startswith('play.google.com/store/apps/'):
        value = 'https://'+value
    parsed = urlsplit(safe_url(value))
    if parsed.hostname == 'play.google.com' and parsed.path == '/store/apps/details':
        return 'package:' + parse_qs(parsed.query).get('id', [''])[0]
    if parsed.hostname == 'market.android.com' and parsed.path == '/details':
        return 'package:' + parse_qs(parsed.query).get('id', [''])[0]
    if parsed.hostname:
        return parsed.hostname.casefold() + parsed.path.rstrip('/') + ('?'+parsed.query if parsed.query else '')
    return 'package:'+value if PACKAGE.fullmatch(value) else value.casefold()


def matches(row, target):
    old_values = {canonical(row.get(k)) for k in ('target','uri') if row.get(k)}
    new_values = {canonical(target.get(k)) for k in ('value','uri','name') if target.get(k)}
    # A curated old package is not enough to match an unrelated name or web URL.
    if row.get('target') and canonical(row['target']) in new_values:
        return 'name'
    if old_values & new_values:
        return 'uri'
    old_package = row.get('package') or package_from(row.get('target'))
    new_package = package_from(target.get('value')) or package_from(target.get('uri'))
    manual = bool(re.search(r'兜底|人工|待验证|候选|fallback|guess',str(row.get('package_source') or ''),re.I))
    if not manual and old_package and new_package and old_package == new_package:
        return 'package'
    if old_package and target.get('android'):
        for value in (target.get('value'), target.get('name')):
            pattern = str(value or '').strip()
            if re.fullmatch(r'[A-Za-z0-9_.*]+',pattern) and '*' in pattern and fnmatch.fnmatchcase(old_package,pattern):
                return 'namespace'
    return ''


def h1(handle):
    obj = session()
    if not getattr(LOCAL,'csrf',None):
        body = get('https://hackerone.com/directory/programs').text
        token = re.search(r'name="csrf-token"\s+content="([^"]+)"',body)
        if not token:
            raise ValueError('Anonymous CSRF initialization unavailable')
        LOCAL.csrf = token[1]
    scopes, program, hashes = [], None, []
    for archived in (False, True):
        after, seen = None, set()
        while True:
            response = obj.post('https://hackerone.com/graphql',json={'query':QUERY,
                    'variables':{'handle':handle,'after':after,'archived':archived}},
                    headers={'X-Csrf-Token':LOCAL.csrf}, timeout=30)
            response.raise_for_status()
            data = response.json()
            if data.get('errors'):
                raise ValueError('Official GraphQL response contains errors')
            team = data['data']['team']
            if not team:
                return {'complete':False,'reason':'program_not_public_or_missing','url':'https://hackerone.com/'+handle}
            program = {k:v for k,v in team.items() if k != 'structured_scopes'}
            connection = team['structured_scopes']
            hashes.append(hashlib.sha256(response.content).hexdigest())
            for row in connection['nodes']:
                if not row or 'asset_identifier' not in row:
                    raise ValueError('Incomplete scope node')
                scopes.append({'value':row['asset_identifier'],'uri':safe_url(row['asset_identifier']),
                               'android':android_target(row) or (row['asset_type']=='OTHER' and bool(re.search(r'\bAndroid\b',row['asset_identifier'],re.I))),
                               'archived':bool(row['archived_at']) or archived,
                               'in_scope':row['eligible_for_submission'] is True,
                               'eligible_for_bounty':row['eligible_for_bounty'],
                               'asset_type':row['asset_type']})
            if not connection['pageInfo']['hasNextPage']:
                break
            after = connection['pageInfo']['endCursor']
            if not after or after in seen:
                raise ValueError('Invalid scope pagination')
            seen.add(after)
    return {'complete':True,'program':program,'scopes':scopes,'sha256':hashes,
            'url':'https://hackerone.com/'+handle,'api_url':'https://hackerone.com/graphql'}


def bugcrowd(handle):
    page = get('https://bugcrowd.com/engagements/'+handle)
    match = re.search(r'data-api-endpoints="([^"]+)"',page.text)
    if not match:
        raise ValueError('Public brief endpoint not available')
    endpoints = json.loads(html.unescape(match[1]))
    path = endpoints['engagementBriefApi']['getBriefVersionDocument']
    if not path.startswith('/engagements/'):
        raise ValueError('Unexpected brief path')
    response = get('https://bugcrowd.com'+path+'.json')
    data = response.json()
    scopes = []
    for group in data['data']['scope']:
        for row in group['targets']:
            rewards = [x.get('max') or 0 for x in (group.get('rewardRangeData') or {}).values() if isinstance(x,dict)]
            scopes.append({'id':row.get('id'),'value':row.get('uri') or row.get('name') or '',
                           'uri':row.get('uri'),'name':row.get('name'),
                           'android':row.get('category') == 'android' or (row.get('category')=='other' and bool(re.search(r'\bAndroid\b',str(row.get('name') or ''),re.I))), 'type':row.get('category'),
                           'in_scope':group['inScope'] is True, 'archived':False,
                           'eligible_for_bounty':max(rewards, default=0)>0})
    return {'complete':True,'url':page.url,'api_url':response.url,'scopes':scopes,
            'program':{'name':data['data']['brief']['name'], 'state':data['data'].get('engagement',{}).get('state'),
                       'status_label':data.get('statusLabel')},
            'sha256':[hashlib.sha256(response.content).hexdigest()]}


def ywh(handle):
    response = get('https://api.yeswehack.com/programs/'+handle)
    data = response.json()
    scopes = [{'value':r['scope'],'android':android_target({'target':r['scope'],'type':r['scope_type']}),
               'type':r['scope_type'],'in_scope':True,'archived':False,'eligible_for_bounty':data.get('bounty')}
              for r in data['scopes']]
    # Rules are also authoritative scope; only exact named Android product bullet lines qualify.
    rules = str(data.get('rules') or '')
    named = [line.strip('-* ').strip() for line in rules.splitlines()
             if re.match(r'^\s*[-*]\s+[^\n]+\(Android(?:[,，\s)]|$)',line,re.I)]
    section = ''
    for line in rules.splitlines():
        if line.startswith('#'):
            section = line.lower()
        if re.search(r'out.of.scope|exclu|不在范围|排除',section,re.I):
            continue
        match = re.match(r'^\s*[-*]\s+\[([^\]]*Android[^\]]*)\]\((https?://play\.google\.com/store/apps/details\?[^)]+)\)',line,re.I)
        if match:
            scopes.append({'value':match[2],'name':match[1],'uri':match[2],'android':True,'in_scope':True,
                           'archived':False,'eligible_for_bounty':data.get('bounty'),'rule_bullet':True})
    return {'complete':True,'url':'https://yeswehack.com/programs/'+handle,'api_url':response.url,
            'program':{'name':data['title'],'bounty':data.get('bounty'),'disabled':data.get('disabled'),
                       'archived':data.get('archived'),'updated_at':data.get('last_update_at')},
            'scopes':scopes,'android_rule_products':named,
            'sha256':[hashlib.sha256(response.content).hexdigest()]}


def classify(row, evidence):
    if not evidence.get('complete'):
        return {'status':'unavailable','reason':evidence.get('reason','official_source_unavailable')}
    targets = [dict(t) for t in evidence['scopes']]
    for target in targets:
        if re.search(r'\bAndroid\b',str(target.get('name') or target.get('value') or ''),re.I) and urlsplit(safe_url(target.get('uri'))).hostname != 'apps.apple.com':
            target['android'] = True
    hits = [(t,matches(row,t)) for t in targets]
    hits = [(t,method) for t,method in hits if method]
    # Explicit present exclusions override an active inclusion; archive cannot override current inclusion.
    rank = {'name':0,'uri':1,'package':2,'namespace':3}
    ordered = sorted(hits,key=lambda x:(x[0].get('archived',False),rank[x[1]],x[0].get('in_scope',True),not x[0].get('android')))
    if ordered:
        target, method = ordered[0]
        if target.get('archived'):
            status = 'archived'
        elif not target.get('in_scope'):
            status = 'out_of_scope'
        else:
            status = 'in_scope' if target.get('android') else 'android_unresolved'
            if not target.get('android') and (target.get('type')=='ios' or target.get('asset_type') in ('APPLE_STORE_APP_ID','OTHER_IPA')):
                status = 'not_android'
            if not target.get('android') and (target.get('asset_type')=='URL' or target.get('type')=='website'):
                status = 'not_android'
        return {'status':status,'match_method':method,'official_target':target}
    label = re.split(r'[（(]',str(row.get('target') or ''))[0].strip().casefold()
    for product in evidence.get('android_rule_products',[]):
        if product.split('(')[0].strip().casefold() == label:
            return {'status':'in_scope','match_method':'android_rule_bullet','official_target':{'value':product,'android':True,
                    'in_scope':True,'eligible_for_bounty':evidence['program'].get('bounty')}}
    return {'status':'not_listed','reason':'not_in_complete_current_or_archived_structured_scope'}


def run(base,cache_dir,workers=4):
    started = now()
    cache_dir.mkdir(parents=True,exist_ok=True)
    datasets, selected = {}, []
    for platform,_,filename,_ in PLATFORMS:
        if platform not in ('h1','bugcrowd','ywh'):
            continue
        records = json.loads((base/'赏金APK'/filename).read_text(encoding='utf-8'))
        datasets[platform] = (filename,records)
        selected.extend((platform,i,row) for i,row in enumerate(records)
                        if row.get('scope_observation')=='historical' or row.get('scope_review_status'))
    programs = sorted({(platform,str(row.get('handle') or row.get('slug'))) for platform,_,row in selected})
    def fetch(key):
        platform,handle = key
        cache = cache_dir/(platform+'-'+handle+'.json')
        if cache.exists():
            return key,json.loads(cache.read_text(encoding='utf-8'))
        try:
            result = {'h1':h1,'bugcrowd':bugcrowd,'ywh':ywh}[platform](handle)
        except (requests.RequestException,ValueError,KeyError,TypeError) as error:
            result = {'complete':False,'reason':type(error).__name__,'url':
                      ('https://hackerone.com/' if platform=='h1' else 'https://bugcrowd.com/engagements/' if platform=='bugcrowd' else 'https://yeswehack.com/programs/')+handle}
        result['observed_at'] = now()
        write(cache,json.dumps(result,ensure_ascii=False,indent=1)+'\n')
        return key,result
    with ThreadPoolExecutor(workers) as executor:
        evidence = dict(executor.map(fetch, programs))
    reviews = []
    for platform,index,row in selected:
        handle = str(row.get('handle') or row.get('slug'))
        source = evidence[(platform,handle)]
        result = classify(row,source)
        review = {'platform':platform,'handle':handle,'target':row.get('target'),'package':row.get('rejected_package_hint') or row.get('package'),
                  **result,'checked_at':source.get('observed_at',started),'source_url':source.get('api_url') or source['url'],
                  'source_sha256':source.get('sha256',[]),'program':source.get('program',{})}
        reviews.append(review)
        row.update(scope_review_status=result['status'],scope_checked_at=review['checked_at'],
                   scope_review_source=review['source_url'],scope_review_reason=result.get('reason') or result.get('match_method'))
        if result['status'] != 'unavailable':
            row['scope_observation'] = 'reviewed'
        row['program_submission_state'] = source.get('program',{}).get('submission_state')
        target = result.get('official_target') or {}
        exact_package = next((package_from(target.get(k)) for k in ('value','uri','name') if package_from(target.get(k))), '')
        if exact_package and row.get('package') == exact_package and target.get('android'):
            row['package_source'] = 'Play链接' if urlsplit(safe_url(target.get('uri'))).hostname == 'play.google.com' else 'scope包名'
            row['package_review_status'] = 'scope_value_confirmed'
        elif result['status']=='not_android' or (result['status']=='android_unresolved' and re.search(r'兜底|人工|候选',str(row.get('package_source') or ''))):
            row['rejected_package_hint'] = row.get('rejected_package_hint') or row.get('package')
            for field in ('package','play','apkpure_apk','apkpure_xapk'):
                row[field] = None
            row['package_review_status'] = 'mapping_not_supported_by_official_target'
        elif result.get('match_method')=='namespace':
            row['package_source'] = '范围通配符内包名待验证'
        if result['status']=='in_scope':
            target = result['official_target']
            row['eligible_for_bounty'] = target.get('eligible_for_bounty')
            if platform=='h1':
                row.update(offers_bounties=source['program'].get('offers_bounties'),
                           submission_state=source['program'].get('submission_state'),eligible_for_submission=True,archived=False)
        # Preserve original fields for provenance; rendering must use the review state.
    report = {'reviewed_at':now(),'baseline_targets':len(selected),'programs_queried':len(programs),
              'status_counts':dict(Counter(r['status'] for r in reviews)),
              'program_state_counts':dict(Counter(r['program'].get('submission_state') or r['program'].get('status_label') or 'other' for r in reviews)),
              'rows':reviews,'limits':['not_listed is not an explicit exclusion or removal verdict.',
                                     'Scope matching does not verify a manually guessed package or an APK download.',
                                     'Unavailable private/deleted programs remain unresolved; no authentication is bypassed.']}
    for filename,records in datasets.values():
        write(base/'赏金APK'/filename,json.dumps(records,ensure_ascii=False,indent=1)+'\n')
    write(base/'赏金APK/history-review.json',json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    coverage_path = base/'赏金APK/coverage.json'
    if coverage_path.exists():
        coverage = json.loads(coverage_path.read_text(encoding='utf-8'))
        for item in coverage['platforms']:
            records = datasets.get(item['platform'], ('',[]))[1]
            if records:
                item.setdefault('historical_before_official_review',item['historical_unconfirmed'])
                item['historical_unconfirmed'] = sum(r.get('scope_observation')=='historical' for r in records)
                item['officially_reviewed'] = sum(bool(r.get('scope_review_status')) for r in records)
                item['review_status_counts'] = dict(Counter(r['scope_review_status'] for r in records if r.get('scope_review_status')))
        coverage['official_review_at'] = report['reviewed_at']
        write(coverage_path,json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
    return {k:v for k,v in report.items() if k not in ('rows','limits')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--cache-dir',type=Path,required=True)
    parser.add_argument('--workers',type=int,default=4)
    args = parser.parse_args()
    print(json.dumps(run(args.base,args.cache_dir,args.workers),ensure_ascii=False,indent=2))
