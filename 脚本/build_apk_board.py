"""Build a readable, theme-aware APK directory from public JSON snapshots. No network."""
import argparse
import csv
import html
import io
import json
import os
import re
import shutil
import time
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit

PLATFORMS = [
    ('bugcrowd','Bugcrowd','apk_final.json','Bugcrowd赏金APK直达清单.md'),
    ('ywh','YesWeHack','ywh_android.json','YWH_APK清单.md'),
    ('h1','HackerOne','h1_android.json','H1_APK清单.md'),
    ('intigriti','Intigriti','intigriti_android.json','Intigriti_APK清单.md'),
    ('src','国内 SRC','src_android.json','国内SRC_APK清单.md'),
]
PACKAGE = re.compile(r'[A-Za-z_][A-Za-z_0-9]*(?:\.[A-Za-z_][A-Za-z_0-9]*)+')


def write(path, content):
    path.parent.mkdir(parents=True,exist_ok=True)
    data = content.encode('utf-8')
    if path.is_file() and path.read_bytes() == data:
        return
    temporary = path.with_name(path.name+'.tmp')
    temporary.write_bytes(data)
    temporary.replace(path)


def safe_url(value):
    value = str(value or '').strip()
    try:
        parsed = urlsplit(value)
        return value if parsed.scheme in ('http','https') and parsed.hostname and not parsed.username and not parsed.password else ''
    except ValueError:
        return ''


def normalize(platform, record):
    handle = str(record.get('handle') or record.get('slug') or '')
    if platform == 'bugcrowd':
        program = record.get('program') or handle
        url = 'https://bugcrowd.com/engagements/'+quote(handle,safe='')
        bounty = {'cash':'cash','points':'points'}.get(record.get('bounty_type'),'unknown')
    elif platform == 'ywh':
        program = record.get('name') or handle
        url = 'https://yeswehack.com/programs/'+quote(handle,safe='')
        bounty = {'bounty':'cash','vdp':'vdp'}.get(record.get('bounty_type'),'unknown')
        if record.get('archived') or record.get('disabled'):
            bounty = 'inactive'
    elif platform == 'h1':
        program = record.get('name') or handle
        url = 'https://hackerone.com/'+quote(handle,safe='')
        if record.get('archived') is True or record.get('eligible_for_submission') is False or record.get('submission_state') == 'closed':
            bounty = 'inactive'
        elif record.get('offers_bounties') is True and record.get('eligible_for_bounty') is True:
            bounty = 'cash'
        elif record.get('offers_bounties') is False or record.get('eligible_for_bounty') is False:
            bounty = 'vdp'
        else:
            bounty = 'unknown'
    elif platform == 'intigriti':
        program = record.get('name') or handle
        url = safe_url(record.get('program_url')) or 'https://app.intigriti.com/programs/'+quote(str(record.get('company') or ''),safe='')+'/'+quote(handle,safe='')
        bounty = {'bounty':'cash','vdp':'vdp'}.get(record.get('bounty_type'),'unknown')
        if record.get('eligible_for_bounty') is False:
            bounty = 'vdp'
        if record.get('status') and record['status'] != 'open':
            bounty = 'inactive'
    else:
        program = record.get('program') or record.get('name') or handle
        url = safe_url(record.get('program_url')) or safe_url(record.get('scope_source'))
        bounty = record.get('bounty_type') if record.get('bounty_type') in ('cash','points','vdp') else 'unknown'
    review = record.get('scope_review_status')
    scope_status = review or record.get('scope_status') or ('source_listed' if record.get('scope_observation')=='observed' else 'unavailable' if record.get('scope_observation')=='historical' else 'unreviewed')
    program_state = record.get('program_submission_state') or record.get('submission_state') or ''
    if review in ('out_of_scope','not_android'):
        bounty = 'excluded'
    elif review == 'archived' or program_state in ('paused','disabled','closed'):
        bounty = 'inactive'
    elif scope_status in ('android_unresolved','product_rename','not_listed','unavailable'):
        bounty = 'unknown'
    raw_package = str(record.get('package') or '').strip()
    package = raw_package if PACKAGE.fullmatch(raw_package) else ''
    play = safe_url(record.get('play'))
    if play and urlsplit(play).hostname != 'play.google.com':
        play = ''
    origin = str(record.get('package_source') or '')
    needs_review = bool(re.search(r'兜底|人工|待验证|候选|fallback|guess',origin,re.I)) or bool(record.get('needs_review'))
    if package:
        play = play or 'https://play.google.com/store/apps/details?id='+quote(package,safe='.')
    source = 'manual' if needs_review else 'scope' if origin == 'scope包名' else 'unspecified'
    for field in ('uri','target','play'):
        raw = safe_url(record.get(field))
        parsed = urlsplit(raw)
        if package and parsed.hostname == 'play.google.com' and parse_qs(parsed.query).get('id') == [package] and not needs_review:
            source = 'play'
    target = str(record.get('target') or record.get('asset_type') or program)
    if target and not target.strip('█\u2588 \t\n'):
        target = '详情以项目页为准'
    reward = str(record.get('reward') or '')
    return {
        'platform':platform,'program':str(program),'url':url,'bounty':bounty,'reward':reward,
        'target':target,'package':package,'package_hint':raw_package if not package else '',
        'package_source':source,'needs_review':needs_review,
        'play':play,'apk_direct':safe_url(record.get('apk_direct')),
        'xapk':(safe_url(record.get('apkpure_xapk')) or 'https://d.apkpure.com/b/XAPK/'+quote(package,safe='.')+'?version=latest') if package else '',
        'apk':(safe_url(record.get('apkpure_apk')) or 'https://d.apkpure.com/b/APK/'+quote(package,safe='.')+'?version=latest') if package else '',
        'download_verified':False,
        'scope_observation':record.get('scope_observation','historical'),
        'scope_observed_at':str(record.get('scope_observed_at') or ''),
        'scope_source':safe_url(record.get('scope_source')),
        'scope_status':scope_status,'scope_checked_at':str(record.get('scope_checked_at') or record.get('scope_observed_at') or ''),
        'scope_review_source':safe_url(record.get('scope_review_source')),
        'program_state':program_state,
        'vendor':str(record.get('vendor') or ''),'reward_conditions':str(record.get('reward_conditions') or ''),
        'download_page':safe_url(record.get('download_page')),
        'package_source_url':safe_url(record.get('package_source_url')),
        'scope_evidence':str(record.get('scope_evidence') or ''),
        'download_state':str(record.get('download_state') or ''),
        'download_notes':str(record.get('download_notes') or ''),
    }


def scope_label(row):
    status = row['scope_status']
    label = {'in_scope':'官方范围内','source_listed':'本轮来源列入','archived':'官方已归档','out_of_scope':'官方明确范围外',
             'not_android':'官方条目非 Android','android_unresolved':'范围有记录 · Android 对应待核',
             'not_listed':'当前官方范围未列出','unavailable':'官方来源待确认','product_rename':'产品更名对应待核','unreviewed':'未逐项核查'}.get(status,'待核查')
    if row.get('program_state') in ('paused','disabled','closed'):
        label += ' · 项目暂停 / 不接收'
    return label


def row_html(row):
    e = lambda value: html.escape(str(value or ''),quote=True)
    label = {'cash':'有赏金','vdp':'VDP / 无赏金','points':'积分','inactive':'已归档 / 不接收','unknown':'待确认','excluded':'范围外 / 非 Android'}[row['bounty']]
    platform = dict((key,name) for key,name,*_ in PLATFORMS)[row['platform']]
    links = [('项目页',row['url']),('核查证据',row['scope_review_source']),('范围来源',row['scope_source']),('官方下载页',row['download_page']),('Google Play',row['play']),('来源 APK',row['apk_direct']),('XAPK 候选',row['xapk']),('APK 候选',row['apk'])]
    anchors = ''.join('<a href="%s">%s ↗</a>'%(e(url),text) for text,url in links if url)
    target = row['target']
    if safe_url(target) and urlsplit(target).hostname == 'play.google.com':
        target = 'Google Play 应用'
    elif row['package'] and target == row['package']:
        target = 'Android 应用'
    observation = scope_label(row)
    return ('<tr><td><a class="program-link" href="%s">%s ↗</a><div class="apk-meta">%s · %s</div><div class="apk-meta">%s</div></td>'
            '<td><div class="target-text">%s</div><code class="package">%s</code></td>'
            '<td><span class="reward-badge">%s</span><div class="apk-meta">%s</div></td>'
            '<td><div class="apk-links">%s</div></td></tr>') % (e(row['url']),e(row['program']),platform,label,observation,e(target),e(row['package'] or '包名待补充'),label,e(row['reward']),anchors)


def build_apk_board(base):
    base = Path(base).resolve()
    out = base / '赏金APK'
    if not any((out / filename).exists() for _,_,filename,_ in PLATFORMS):
        return None
    metadata = out / 'snapshot.json'
    if metadata.exists():
        stamp = json.loads(metadata.read_text(encoding='utf-8')).get('generated_at','未记录')
    else:
        old = (out / '赏金APK看板.html').read_text(encoding='utf-8') if (out / '赏金APK看板.html').exists() else ''
        match = re.search(r'(?:Generated：|Generated:|数据快照：)(\d{4}-\d\d-\d\d \d\d:\d\d)',old)
        stamp = match[1] if match else '未记录'
        write(metadata,json.dumps({'generated_at':stamp},ensure_ascii=False,indent=2)+'\n')
    rows = []
    for key,_,filename,_ in PLATFORMS:
        path = out / filename
        if path.exists():
            rows.extend(normalize(key,row) for row in json.loads(path.read_text(encoding='utf-8')))
    rows.sort(key=lambda row:(row['program'].casefold(),row['platform'],row['package'],row['target']))
    counts = Counter(row['bounty'] for row in rows)
    platforms = [{
        'key':key,'name':name,'targets':sum(row['platform']==key for row in rows),
        'cash':sum(row['platform']==key and row['bounty']=='cash' for row in rows),
        'entries':sum(row['platform']==key and bool(row['play'] or row['apk_direct'] or row['xapk'] or row['download_page']) for row in rows),
    } for key,name,_,_ in PLATFORMS]
    stats = {'generated_at':stamp,'targets':len(rows),'programs':len({(r['platform'],r['url']) for r in rows}),
             'unique_packages':len({r['package'] for r in rows if r['package']}),
             'observed':sum(r['scope_observation']=='observed' for r in rows),
             'reviewed':sum(r['scope_observation']=='reviewed' for r in rows),
             'scope_counts':dict(Counter(r['scope_status'] for r in rows)),
             'packages':sum(bool(r['package']) for r in rows),'cash':counts['cash'],'platforms':platforms,'bounty_counts':dict(counts)}
    write(out / 'dashboard.json',json.dumps({'stats':stats,'rows':rows},ensure_ascii=False,separators=(',',':'))+'\n')
    buffer = io.StringIO(newline='')
    writer = csv.writer(buffer,lineterminator='\n')
    columns = ['platform','program','bounty','reward','target','package','package_source','needs_review','url','play','apk_direct','xapk','apk','download_verified','scope_observation','scope_observed_at','scope_source','scope_status','scope_checked_at','scope_review_source','program_state','vendor','reward_conditions','download_page','package_source_url']
    writer.writerow(columns)
    for row in rows:
        # Prevent a downloaded spreadsheet from interpreting source text as a formula.
        writer.writerow("'"+str(row.get(k,'')) if str(row.get(k,'')).startswith(('=','+','-','@')) else row.get(k,'') for k in columns)
    write(out / 'dashboard.csv','\ufeff'+buffer.getvalue())
    cards = ''.join('<button class="platform-card" type="button" data-platform="%s"><b>%s</b><strong>%s</strong><span>%s 有赏金 / %s 个入口</span></button>'%(p['key'],p['name'],p['targets'],p['cash'],p['entries']) for p in platforms)
    template = Path(__file__).with_name('apk_dashboard.html').read_text(encoding='utf-8')
    replacements = {'@@ROWS@@':'',
                    '@@PLATFORMS@@':cards,'@@TOTAL@@':str(stats['targets']),'@@CASH@@':str(stats['cash']),
                    '@@PACKAGES@@':str(stats['packages']),'@@PROGRAMS@@':str(stats['programs']),'@@TIME@@':html.escape(stamp)}
    replacements['@@ROWS@@'] = ''.join(row_html(row) for row in [r for r in rows if r['bounty']=='cash'][:25])
    for key,value in replacements.items():
        template = template.replace(key,value)
    write(out / '赏金APK看板.html',template)
    write(out / 'index.html','<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=./赏金APK看板.html"><a href="./赏金APK看板.html">Android APK 目录</a></html>\n')
    readme = ['# Android APK 与赏金项目目录','',
              '[打开在线目录](https://8eeth0ven.github.io/security-md-collect/赏金APK/赏金APK看板.html) · [返回主页](../README.md) · [CSV](dashboard.csv) · [JSON](dashboard.json)','',
              '默认明亮，支持深色与跟随系统、中英文切换、平台/赏金/入口筛选和分页。首屏静态输出前 25 条有赏金记录，JavaScript 不可用时也能阅读。','',
              '> 快照整理时间：%s。这里只整理公开元数据，不下载 APK、不验证第三方下载地址。'%stamp,'',
              '| 平台 | 全部目标 | 有赏金目标 | 有应用入口 |','| --- | ---: | ---: | ---: |']
    readme += ['| %s | %s | %s | %s |'%(p['name'],p['targets'],p['cash'],p['entries']) for p in platforms]
    readme += ['', '## 字段与边界','',
               '- 目标条目数与唯一应用数不同；同一个包名可能属于多个项目或目标。',
               '- 最新来源观察到 %s 条，另有 %s 条历史记录已逐项核对官方范围。唯一有效格式包名 %s 个，尚未逐个验证商店存续。'%(stats['observed'],stats['reviewed'],stats['unique_packages']),
               '- [338 条历史目标核查结果](history-review.json)保留逐项来源与证据；范围外、归档、非 Android 和暂停项目从默认赏金结果中排除。国内 SRC 提供单独的平台筛选与[源证据](src-evidence.json)。',
               '- [覆盖审计](coverage.json)记录来源项目数、Android 范围数、未解析包名与历史缺口；[来源目标快照](source-observations.json)保留本轮抽取证据。[国内 SRC 待核清单](../docs/coverage.md)单列，尚未冒充完整 APK 库。',
               '- “有赏金”依据快照的明确字段；HackerOne 同时要求计划有赏金且目标符合赏金资格，归档/不接收记录单独标注。积分、VDP 和未知状态不会默认算作有赏金。',
               '- Google Play 为应用商店入口；APKPure 为第三方镜像候选。生成候选 URL 不等于验证下载成功，`download_verified` 当前全部为 false。',
               '- 包名来源分为 Play 链接提取、人工映射待核对和未标注；无包名时保留项目页入口。',
               '- 快照不等于当前赏金范围，研究前核对项目官方页面。',
               '- 原始四平台 JSON 与清单保留在本目录。运行 `python 脚本/build_apk_board.py` 可离线重建。','']
    write(out / 'README.md','\n'.join(readme))
    for key, name, filename, markdown in PLATFORMS:
        selected = [r for r in rows if r['platform']==key]
        lines = ['# '+name+' Android 范围清单', '',
                 '[打开在线筛选](https://8eeth0ven.github.io/security-md-collect/赏金APK/赏金APK看板.html?platform='+key+'&bounty=all) · [原始记录]('+filename+') · [覆盖审计](../docs/coverage.md)', '',
                 '目标记录 %s 条；唯一有效格式包名 %s 个。快照整理时间：%s。'%(len(selected),len({r['package'] for r in selected if r['package']}),stamp), '',
                 '赏金状态基于各次快照；历史待核不代表当前仍在范围。镜像未验证，范围和维护版本以官方页面为准。', '',
                 '| 项目 | 目标 / 包名 | 赏金状态 | 来源观察 |', '| --- | --- | --- | --- |']
        for row in selected:
            clean = lambda x: str(x or '').replace('|','\\|').replace('\n',' ').replace('\r',' ')
            state = {'cash':'快照有赏金','vdp':'VDP / 无赏金','points':'积分','unknown':'待确认','inactive':'归档 / 不接收','excluded':'范围外 / 非 Android'}[row['bounty']]
            observed = scope_label(row)
            lines.append('| [%s](%s) | %s | %s | %s |'%(clean(row['program']),row['url'],clean(row['package'] or row['target']),state,observed))
        write(out/markdown,'\n'.join(lines)+'\n')
    return stats


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,default=Path(os.environ.get('SECMD_BASE') or Path(__file__).resolve().parents[1]))
    parser.add_argument('--source',type=Path,help='Optional directory containing the four public source JSON files')
    args = parser.parse_args()
    if args.source:
        out = args.base / '赏金APK'
        out.mkdir(parents=True,exist_ok=True)
        for _,_,filename,markdown in PLATFORMS:
            for name in (filename,markdown):
                file = args.source / name
                if file.is_file() and file.resolve() != (out / name).resolve():
                    shutil.copy2(file,out / name)
        write(out / 'snapshot.json',json.dumps({'generated_at':time.strftime('%Y-%m-%d %H:%M')},ensure_ascii=False,indent=2)+'\n')
    source_root = Path(__file__).resolve().parents[1]
    if source_root != args.base.resolve():
        shutil.copytree(source_root / 'web',args.base / 'web',dirs_exist_ok=True)
    stats = build_apk_board(args.base)
    print('APK directory built: %s targets' % (stats['targets'] if stats else 0))
