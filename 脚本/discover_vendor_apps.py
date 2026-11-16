"""Discover Android candidates for mapped vendors without asserting SRC eligibility.

Qimai is probed anonymously first. If access is unavailable, that limitation is
recorded explicitly and public Tencent MyApp search/detail pages are used.
Only the actual search-result card is parsed; PC entries, mini games and
recommendations are excluded. Publisher-name matches remain candidates.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import threading
from urllib.parse import quote

import requests

PACKAGE = re.compile(r'[A-Za-z]\w*(?:\.[A-Za-z]\w*)+')
NEXT = re.compile(rb'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)
ALIASES = {
    '腾讯':['腾讯','tencent'], '阿里巴巴':['阿里','淘宝','天猫','钉钉','优酷','高德','闲鱼','饿了么','飞猪','夸克','alibaba'],
    '蚂蚁集团':['蚂蚁','支付宝','口碑','网商银行'], '字节跳动':['字节','抖音','今日头条','脸萌','飞书'],
    '百度':['百度','baidu'], '网易':['网易','netease'], '小米':['小米','xiaomi','多看'],
    'OPPO':['oppo','欧珀','欢太','heytap'], 'vivo':['vivo','维沃'], '一加':['一加','oneplus'],
    'realme':['realme','锐尔觅'], '华为':['华为','huawei'], '荣耀':['荣耀','honor'],
    '360':['三六零','奇虎','360'], '滴滴':['滴滴','小桔'], '拼多多':['拼多多','寻梦'],
    '小红书':['行吟','小红书'], '快手':['快手','kuaishou'], '携程':['携程','ctrip'],
    '哔哩哔哩':['哔哩','bilibili'], '京东':['京东','jd.com'], '美团':['美团','三快'],
    '贝壳':['贝壳','链家'], '得物':['得物','识装'], '顺丰':['顺丰'], '金山办公':['金山','wps'],
    '微软':['microsoft','微软'], '谷歌':['google','谷歌'], 'Meta':['meta','facebook','instagram','whatsapp'],
    '亚马逊':['amazon','亚马逊'], '苹果':['apple','苹果'], 'Snap':['snap'], 'Snap (Snapchat)':['snap'],
    'Twitter/X':['twitter','x corp'], 'Netflix':['netflix'], 'Uber':['uber'], 'Airbnb':['airbnb'],
    'PayPal':['paypal'], 'Adobe':['adobe'], '三星':['samsung','三星'],
}
QUERIES = {
    '阿里巴巴':'阿里','蚂蚁集团':'支付宝','字节跳动':'抖音','Meta':'Facebook','谷歌':'Google',
    'Apache软件基金会':'Apache','CNCF云原生基金会':'CNCF','深度求索DeepSeek':'DeepSeek',
    '京东云':'京东','中国电信/天翼云':'天翼','中国移动/移动云':'中国移动','HP/HPE':'HP',
    '奔驰/戴姆勒':'奔驰','Snap (Snapchat)':'Snapchat','Twitter/X':'Twitter',
    'Block (Square/Cash App)':'Cash App','Wise (TransferWise)':'Wise',
}
LOCAL = threading.local()


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def get(url, cache):
    """Cache public response bodies privately; never publish complete page state."""
    key = hashlib.sha256(url.encode()).hexdigest()
    meta, body = cache/(key+'.meta.json'), cache/(key+'.body')
    if meta.exists() and body.exists():
        return json.loads(meta.read_text(encoding='utf-8')), body.read_bytes()
    try:
        if not hasattr(LOCAL, 'session'):
            LOCAL.session = requests.Session()
            LOCAL.session.trust_env = False
        response = LOCAL.session.get(url, timeout=20, headers={'User-Agent':'Mozilla/5.0'})
        data = response.content
        record = {'url':url, 'final_url':response.url, 'http_status':response.status_code,
                  'observed_at':now(), 'sha256':hashlib.sha256(data).hexdigest(),
                  'bytes':len(data), 'content_type':response.headers.get('Content-Type','')}
    except requests.RequestException as error:
        data = b''
        record = {'url':url, 'http_status':0, 'observed_at':now(),
                  'error':type(error).__name__+': '+str(error)[:180]}
    body.write_bytes(data)
    meta.write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return record, data


def components(body):
    match = NEXT.search(body)
    if not match:
        return []
    try:
        return json.loads(match.group(1))['props']['pageProps']['dynamicCardResponse']['data']['components']
    except (ValueError, KeyError, TypeError):
        return []


def android(row):
    return str(row.get('game_type')) == '0' and bool(PACKAGE.fullmatch(row.get('pkg_name',''))) and bool(row.get('name'))


def search_rows(body):
    return [row for card in components(body) if card.get('data',{}).get('name') == 'SearchList'
            for row in card.get('data',{}).get('itemData',[]) if android(row)]


def detail_row(body, package):
    return next((row for card in components(body) for row in card.get('data',{}).get('itemData',[])
                 if row.get('pkg_name') == package and android(row)), None)


def discover(base, cache, workers=6, verify_details=True, seed_file=None):
    cache.mkdir(parents=True, exist_ok=True)
    vendors = json.loads((base/'资产/vendors.json').read_text(encoding='utf-8'))
    qimai_url = 'https://api.qimai.cn/search/index?search=%E8%85%BE%E8%AE%AF&device=android'
    qimai_meta, qimai_body = get(qimai_url, cache)
    try:
        qimai_reply = json.loads(qimai_body)
    except ValueError:
        qimai_reply = {}
    qimai_status = 'public_api_access_error' if qimai_reply.get('code') == 10602 else 'not_integrated_no_verified_export'
    qimai = dict(qimai_meta, api_code=qimai_reply.get('code'), api_message=qimai_reply.get('msg'), status=qimai_status)

    def one(vendor):
        name = vendor['vendor']
        query = QUERIES.get(name, name.split('（')[0].split('(')[0].strip())
        source = 'https://sj.qq.com/search?q='+quote(query)
        meta, body = get(source, cache)
        aliases = ALIASES.get(name, [name.split('（')[0].split('(')[0].split('/')[0].strip()])
        apps = []
        for row in search_rows(body):
            publisher = row.get('developer') or row.get('operator') or ''
            if not any(alias.casefold() in publisher.casefold() for alias in aliases):
                continue
            package = row['pkg_name']
            detail = 'https://sj.qq.com/appdetail/'+package
            detail_meta = None
            if verify_details:
                detail_meta, detail_body = get(detail, cache)
                found = detail_row(detail_body, package)
                if detail_meta.get('http_status') != 200 or found is None:
                    continue
                row = found
            apps.append({'vendor':name, 'name':row['name'], 'package':package, 'platform':'android',
                         'developer':row.get('developer') or row.get('operator') or publisher,
                         'version':row.get('version_name',''), 'discovery_source':'腾讯应用宝',
                         'discovery_source_url':source, 'package_source_url':detail, 'download_page':detail,
                         'download_state':'store_page_verified' if detail_meta else 'store_page_unverified',
                         'scope_status':'unverified', 'ownership_status':'publisher_name_match_needs_review',
                         'observed_at':meta['observed_at'], 'source_sha256':meta.get('sha256'),
                         'detail_metadata':detail_meta,
                         'notes':'发布者名称匹配仅提供厂商归属线索；不是完整开发者目录，SRC范围和奖金需独立核查。'})
        result = {'vendor':name, 'orgs':vendor.get('orgs',[]), 'src':vendor.get('src',''),
                  'qimai_url':'https://www.qimai.cn/search/index/search/'+quote(query),
                  'qimai_status':qimai_status, 'qimai_checked_individually':False,
                  'qimai_evidence_url':qimai_url, 'checked_at':meta['observed_at'], 'sources':[meta],
                  'status':('android_candidates_found' if apps else 'no_publisher_matched_android_in_first_search_page')
                           if meta.get('http_status') == 200 else 'source_unavailable',
                  'candidate_count':len(apps),
                  'notes':'七麦匿名API仅作来源级可用性探测；备用来源实际检索本厂商首屏。零命中不代表没有Android应用。'}
        return result, apps

    rows, apps = [], []
    with ThreadPoolExecutor(max_workers=max(1,min(workers,8))) as pool:
        for row, found in pool.map(one, vendors):
            rows.append(row)
            apps.extend(found)
    # Reviewed search seeds also cover products whose brand differs from the
    # parent company's name. Seeds are identifiers to verify, never scope grants.
    seed_file = seed_file or base/'赏金APK/app-discovery-seeds.json'
    seeds = json.loads(seed_file.read_text(encoding='utf-8')) if seed_file.exists() else []

    def from_seed(seed):
        package = str(seed.get('package') or '')
        if not PACKAGE.fullmatch(package) or not seed.get('vendor'):
            raise ValueError('Android seeds require vendor and a valid package ID')
        detail = 'https://sj.qq.com/appdetail/'+package
        meta, body = get(detail, cache)
        row = detail_row(body, package)
        if meta.get('http_status') != 200 or row is None:
            return None
        return {'vendor':seed['vendor'], 'name':row['name'], 'package':package, 'platform':'android',
                'developer':row.get('developer') or row.get('operator') or '',
                'version':row.get('version_name',''), 'discovery_source':'腾讯应用宝',
                'discovery_source_url':detail, 'package_source_url':detail, 'download_page':detail,
                'download_state':'store_page_verified', 'scope_status':'unverified',
                'ownership_status':'reviewed_seed_needs_scope_review', 'observed_at':meta['observed_at'],
                'source_sha256':meta.get('sha256'), 'detail_metadata':meta,
                'notes':'重点应用种子已核Android详情；集团归属、当前SRC范围和奖金须独立核查。'}

    with ThreadPoolExecutor(max_workers=max(1,min(workers,8))) as pool:
        apps.extend(row for row in pool.map(from_seed, seeds) if row)
    apps = list({(app['vendor'],app['package']):app for app in apps}.values())
    # An explicit SRC inventory is separate evidence, not inferred from MyApp.
    reviewed = base/'赏金APK/src_android.json'
    confirmed = {(row.get('vendor'),row.get('package')):row
                 for row in json.loads(reviewed.read_text(encoding='utf-8'))
                 if row.get('package') and row.get('scope_status') == 'in_scope'} if reviewed.exists() else {}
    for app in apps:
        record = confirmed.get((app['vendor'],app['package']))
        if record:
            app.update(scope_status='confirmed', scope_match_type=record.get('scope_match_type','named_product'),
                       scope_source=record.get('scope_source'), scope_review_source=record.get('scope_review_source'),
                       scope_observed_at=record.get('scope_observed_at'),
                       program_state=record.get('program_state','unknown'),
                       submission_state=record.get('submission_state','unknown'),
                       notes=record.get('scope_notes') or record.get('scope_evidence') or app['notes'])
    for row in rows:
        row['candidate_count'] = sum(app['vendor'] == row['vendor'] for app in apps)
        if row['candidate_count']:
            row['status'] = 'android_candidates_found'
    mapped = {row['vendor'] for row in rows}
    additional = sorted({app['vendor'] for app in apps} - mapped)
    backlog = base/'赏金APK/src-backlog.json'
    official_checks = json.loads(backlog.read_text(encoding='utf-8')).get('official_src_checks',[]) if backlog.exists() else []
    return {'generated_at':now(), 'vendors':rows, 'apps':apps, 'qimai_probe':qimai,
            'official_src_checks':official_checks,
            'additional_vendors':[{'vendor':name, 'status':'android_candidates_found',
                                   'candidate_count':sum(app['vendor']==name for app in apps),
                                   'notes':'补充的Android重点应用厂商，未计入GitHub映射分母。'} for name in additional],
            'summary':{'mapped_vendors':len(rows), 'vendors_checked':len(rows),
                       'vendors_with_candidates':sum(row['candidate_count'] > 0 for row in rows),
                       'candidate_apps':len(apps), 'qimai_access_status':qimai_status,
                       'qimai_individual_vendor_queries':0,
                       'additional_domestic_vendors':len(additional),
                       'scope_confirmed_apps':sum(app['scope_status']=='confirmed' for app in apps),
                       'scope_unverified_apps':sum(app['scope_status']!='confirmed' for app in apps),
                       'detail_verified_apps':sum(app.get('download_state')=='store_page_verified' for app in apps),
                       'source_unavailable':sum(row['status']=='source_unavailable' for row in rows)},
            'limits':['七麦来源不可访问时不声称已获取七麦应用或完成逐厂商七麦查询。',
                      '备用来源只检索厂商名称首屏，非厂商完整应用全集；零命中不代表没有应用。',
                      '候选记录不证明集团归属、SRC范围、当前可提交或现金奖励。',
                      '仅验证应用详情和Android标识；没有下载APK、校验签名或包体。',
                      '缓存保留真实来源观察时间；generated_at是整理时间，重新在线核查应使用新缓存目录。']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--cache-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--workers', type=int, default=6)
    parser.add_argument('--seeds', type=Path, help='Reviewed vendor/package JSON identifiers to verify')
    parser.add_argument('--skip-detail-verification', action='store_true')
    args = parser.parse_args()
    result = discover(args.base.resolve(), args.cache_dir.resolve(), args.workers, not args.skip_detail_verification, args.seeds)
    output = args.output or args.base/'赏金APK/vendor-app-discovery.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result['summary'],ensure_ascii=False))
