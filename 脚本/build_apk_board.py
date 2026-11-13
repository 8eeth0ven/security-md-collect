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
    elif platform == 'h1':
        program = record.get('name') or handle
        url = 'https://hackerone.com/'+quote(handle,safe='')
        if record.get('archived') is True or record.get('eligible_for_submission') is False:
            bounty = 'inactive'
        elif record.get('offers_bounties') is True and record.get('eligible_for_bounty') is True:
            bounty = 'cash'
        elif record.get('offers_bounties') is False or record.get('eligible_for_bounty') is False:
            bounty = 'vdp'
        else:
            bounty = 'unknown'
    else:
        program = record.get('name') or handle
        url = safe_url(record.get('program_url')) or 'https://app.intigriti.com/programs/'+quote(str(record.get('company') or ''),safe='')+'/'+quote(handle,safe='')
        bounty = {'bounty':'cash','vdp':'vdp'}.get(record.get('bounty_type'),'unknown')
    raw_package = str(record.get('package') or '').strip()
    package = raw_package if PACKAGE.fullmatch(raw_package) else ''
    play = safe_url(record.get('play'))
    origin = str(record.get('package_source') or '')
    needs_review = bool(re.search(r'兜底|人工|待验证|候选|fallback|guess',origin,re.I))
    if package:
        play = play or 'https://play.google.com/store/apps/details?id='+quote(package,safe='.')
    source = 'manual' if needs_review else 'unspecified'
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
    }


def row_html(row):
    e = lambda value: html.escape(str(value or ''),quote=True)
    label = {'cash':'有赏金','vdp':'VDP / 无赏金','points':'积分','inactive':'已归档 / 不接收','unknown':'待确认'}[row['bounty']]
    platform = dict((key,name) for key,name,*_ in PLATFORMS)[row['platform']]
    links = [('项目页',row['url']),('Google Play',row['play']),('来源 APK',row['apk_direct']),('XAPK 候选',row['xapk']),('APK 候选',row['apk'])]
    anchors = ''.join('<a href="%s">%s ↗</a>'%(e(url),text) for text,url in links if url)
    target = row['target']
    if safe_url(target) and urlsplit(target).hostname == 'play.google.com':
        target = 'Google Play 应用'
    elif row['package'] and target == row['package']:
        target = 'Android 应用'
    return ('<tr><td><a class="program-link" href="%s">%s ↗</a><div class="apk-meta">%s · %s</div></td>'
            '<td><div class="target-text">%s</div><code class="package">%s</code></td>'
            '<td><span class="reward-badge">%s</span><div class="apk-meta">%s</div></td>'
            '<td><div class="apk-links">%s</div></td></tr>') % (e(row['url']),e(row['program']),platform,label,e(target),e(row['package'] or '包名待补充'),label,e(row['reward']),anchors)


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
        'entries':sum(row['platform']==key and bool(row['play'] or row['apk_direct'] or row['xapk']) for row in rows),
    } for key,name,_,_ in PLATFORMS]
    stats = {'generated_at':stamp,'targets':len(rows),'programs':len({(r['platform'],r['url']) for r in rows}),
             'packages':sum(bool(r['package']) for r in rows),'cash':counts['cash'],'platforms':platforms,'bounty_counts':dict(counts)}
    write(out / 'dashboard.json',json.dumps({'stats':stats,'rows':rows},ensure_ascii=False,separators=(',',':'))+'\n')
    buffer = io.StringIO(newline='')
    writer = csv.writer(buffer,lineterminator='\n')
    columns = ['platform','program','bounty','reward','target','package','package_source','needs_review','url','play','apk_direct','xapk','apk','download_verified']
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
               '- “有赏金”依据快照的明确字段；HackerOne 同时要求计划有赏金且目标符合赏金资格，归档/不接收记录单独标注。积分、VDP 和未知状态不会默认算作有赏金。',
               '- Google Play 为应用商店入口；APKPure 为第三方镜像候选。生成候选 URL 不等于验证下载成功，`download_verified` 当前全部为 false。',
               '- 包名来源分为 Play 链接提取、人工映射待核对和未标注；无包名时保留项目页入口。',
               '- 快照不等于当前赏金范围，研究前核对项目官方页面。',
               '- 原始四平台 JSON 与清单保留在本目录。运行 `python 脚本/build_apk_board.py` 可离线重建。','']
    write(out / 'README.md','\n'.join(readme))
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
