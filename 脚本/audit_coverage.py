"""Build an honest coverage report from public snapshots and optional local state."""
import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from build_apk_board import build_apk_board, write


def load(path, default):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default


def audit(base, collector=None):
    previous = load(base/'索引/coverage.json', {})
    records = [r for file in (base/'厂商').glob('*/repos.json') for r in load(file, [])
               if r.get('sec_path') and r['sec_path'] != 'error']
    vendors = load(base/'资产/vendors.json', [])
    owners = {o.casefold() for v in vendors for o in v['orgs']}
    local = {p.parent.name.casefold() for p in (base/'厂商').glob('*/*/SECURITY.md')}
    policy = {'mapped_vendors': len(vendors), 'mapped_accounts': len(owners), 'policy_records': len(records),
              'local_documents': sum(r['full_name'].replace('/','__').casefold() in local for r in records),
              'default_policy_repositories': sum(r['full_name'].endswith('/.github') for r in records),
              'global_coverage_percent': None,
              'limits': ['Only mapped accounts and discovered repositories, not all GitHub.',
                         'Account default documents are counted once, not expanded across inheriting repos.',
                         'Successful listing does not prove all upstream repositories were enumerated.']}
    if collector:
        if not (collector/'索引/state.json').is_file() or not (collector/'索引/orgs').is_dir():
            raise ValueError('Collector state and repository catalog are required; missing files cannot be counted as zero pending.')
        state = load(collector/'索引/state.json', {})
        catalog = {full.casefold() for file in (collector/'索引/orgs').glob('*.json') for full in load(file,{})}
        checked = {full.casefold() for full in state.get('repos_checked', {})}
        policy.update(known_catalog_repositories=len(catalog), checked_in_known_catalog=len(catalog & checked),
                      never_checked_in_known_catalog=len(catalog-checked),
                      accounts_with_listing_failures=sum(bool(v.get('fail_count')) for v in state.get('orgs',{}).values()),
                      accounts_with_truncated_search=sum(bool(v.get('truncated')) for v in state.get('orgs',{}).values()))
        quarantine = load(base/'索引/retry-candidates.json', [])
        policy['historical_error_rechecks'] = dict(Counter(
            'policy_found' if r['full_name'] in state.get('repos_data', {}) else
            'confirmed_absent' if r['full_name'] in state.get('repos_checked', {}) else 'unresolved'
            for r in quarantine))
        pending = sorted(catalog-checked)
        write(base/'索引/待检查仓库.json', json.dumps({
            'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'status': 'measured_from_local_collector', 'repositories': pending,
            'count': len(pending)}, ensure_ascii=False, indent=2)+'\n')
    else:
        old = previous.get('security_md', {})
        historical = old.get('historical_catalog_summary')
        if not historical and 'never_checked_in_known_catalog' in old:
            historical = {key: old.get(key) for key in ('known_catalog_repositories',
                'checked_in_known_catalog', 'never_checked_in_known_catalog')}
            historical['observed_at'] = previous.get('generated_at')
        if historical:
            policy['historical_catalog_summary'] = {**historical,
                'status': 'source_manifest_unavailable',
                'note': 'Historical aggregate only. The original state/orgs and per-repository pending list are unavailable; this run does not claim those repositories were completed.'}
    priority = load(base/'索引/重点项目核查.json', {})
    if priority:
        policy['priority_audit'] = {k:v for k,v in priority.items() if k not in ('rows', 'account_defaults')}
    discovery = load(base/'赏金APK/vendor-app-discovery.json', {})
    scope_review = load(base/'赏金APK/scope-review.json', {})
    app_source_coverage = load(base/'赏金APK/app-source-coverage.json', {})
    domestic_records = load(base/'赏金APK/src_android.json', [])
    official_records = load(base/'赏金APK/official_android.json', [])
    review_counts = Counter(r.get('review_status', 'unresolved') for r in scope_review.get('rows', []))
    review_confirmed = review_counts['confirmed_scope'] + review_counts['confirmed_paused']
    review_misattributed = review_counts['ownership_mismatch'] + review_counts['vendor_name_collision']
    review_excluded = review_counts['officially_excluded']
    review_pending = len(scope_review.get('rows', [])) - review_confirmed - review_misattributed - review_excluded
    domestic_summary = {
        'records': len(domestic_records),
        'paused_records': sum(r.get('program_state') == 'paused' for r in domestic_records),
        'program_state_counts': dict(Counter(r.get('program_state', 'unknown') for r in domestic_records)),
        'submission_state_counts': dict(Counter(r.get('submission_state', 'unknown') for r in domestic_records)),
        'independent_official_program_records': len(official_records)}
    review_summary = {
        'manifest': '赏金APK/scope-review.json',
        'generated_at': scope_review.get('generated_at'),
        'baseline_candidates': scope_review.get('baseline_candidates', 0),
        'reviewed_candidates': len(scope_review.get('rows', [])),
        'confirmed_scope': review_confirmed,
        'current_scope_associations': review_counts['confirmed_scope'],
        'confirmed_paused': review_counts['confirmed_paused'],
        'ownership_mismatches': review_misattributed,
        'explicitly_excluded': review_excluded,
        'pending_evidence': review_pending,
        'result_counts': dict(review_counts),
        'limits': scope_review.get('limits', [])}

    apk = build_apk_board(base)
    sources = load(base/'赏金APK/coverage.json', {})
    history = load(base/'赏金APK/history-review.json', {})
    report = {'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
              'security_md': policy, 'android': apk, 'android_sources': sources.get('platforms', []),
              'domestic_src': load(base/'赏金APK/src-backlog.json', {}),'history_review':{k:v for k,v in history.items() if k!='rows'},
              'domestic_src_summary': domestic_summary, 'scope_review_summary': review_summary,
              'app_source_coverage': {k: v for k, v in app_source_coverage.items() if k != 'checks'},
              'verdict': 'Incomplete: measured source coverage, with explicit unresolved and inaccessible scope.'}
    if discovery:
        report['app_discovery'] = {
            'generated_at': discovery.get('generated_at'),
            'vendors': len(discovery.get('vendors', [])), 'apps': len(discovery.get('apps', [])),
            'vendor_status_counts': dict(Counter(r.get('status', 'unknown') for r in discovery.get('vendors', []))),
            'scope_status_counts': dict(Counter(r.get('scope_status', 'unreviewed') for r in discovery.get('apps', []))),
            'limits': discovery.get('limits', [])}
    write(base/'索引/coverage.json', json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    lines = ['# 采集覆盖审计', '', '这份索引尚未覆盖所有 GitHub 安全策略，也未覆盖所有 SRC / 赏金 Android 应用。以下数字有明确来源边界，不宣称全网覆盖率。', '',
             '审计时间：'+report['generated_at'], '', '## SECURITY.md', '',
             '- 映射厂商 %s 个、GitHub 账户 %s 个；策略仓库 %s 个，本地原文 %s 份。'%(len(vendors),len(owners),len(records),policy['local_documents']),
             '- 其中账户 `.github` 默认策略仓库 %s 个；只计一份文档，不按可能继承它的仓库数扩增。'%policy['default_policy_repositories']]
    if collector:
        lines += ['- 已知目录缓存 %s 个仓库，已检查 %s 个，尚未检查 %s 个。这个分母只是本机已经发现的仓库，不能当作 GitHub 的全部仓库。'%(policy['known_catalog_repositories'],policy['checked_in_known_catalog'],policy['never_checked_in_known_catalog'])]
        status = policy['historical_error_rechecks']
        lines += ['- 早前误收录的历史错误档案复核：找到策略 %s 条、确认无策略 %s 条、仍待复核 %s 条；原始档案保留以便追溯。'%(status.get('policy_found',0),status.get('confirmed_absent',0),status.get('unresolved',0))]
        lines += ['- 可重跑的逐仓库待查清单：[待检查仓库.json](../索引/待检查仓库.json)。']
    elif policy.get('historical_catalog_summary'):
        h = policy['historical_catalog_summary']
        lines += ['- 历史采集快照（%s）报告已发现 %s 个仓库、已检查 %s 个、未检查 %s 个。当前机器没有原始 `state.json` / `orgs/` 和这批未检查仓库的明细，不能复现原集合，也不能宣称已经清零。'%(h.get('observed_at','未记录'),h.get('known_catalog_repositories'),h.get('checked_in_known_catalog'),h.get('never_checked_in_known_catalog'))]
    if priority:
        counts = dict(Counter(r.get('result','unresolved') for r in priority.get('rows', [])))
        lines += ['', '### 常见重点项目逐项核查', '',
                  '本轮显式集合 %s 项，结果：%s。完整项目、HTTP证据与重试状态见[重点项目核查](../索引/重点项目核查.json)。这份集合独立于历史 221 项，不能互相替代。'%(len(priority.get('rows', [])), '；'.join('%s %s'%(k,v) for k,v in sorted(counts.items())))]
    lines += ['', '已补账户默认策略与公开范围中明确列出的 GitHub 仓库；已有策略每 7 天、未发现策略每 30 天重查。错误不进入正/负缓存，策略确认为删除后移出当前索引。部分分页失败重试；代码搜索超过 1,000 或 `incomplete_results` 单列，不能宣称扫全。', '',
              '[GitHub 官方继承规则](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file)规定 `.github/` → 根目录 → `docs/`，当前仓库没有时使用账户 `.github` 仓库的默认文件。未映射账户、动态改名、私有仓库、非标准文件名仍是缺口。', '',
              '## Android 范围', '', '| 来源 | 源项目数 | 原始 Android 范围行 | 本轮来源观察 | 历史已官方核查 | 历史未核查 |', '| --- | ---: | ---: | ---: | ---: | ---: |']
    for row in sources.get('platforms', []):
        lines.append('| %s | %s | %s | %s | %s | %s |'%(row['platform'],row['source_programs'],row['android_scopes_in_source'],row['observed_records'],row.get('officially_reviewed',0),row['historical_unconfirmed']))
    if apk:
        lines += ['', '合并目录共 %s 条目标记录、%s 个唯一有效格式包名；目标记录不等于应用数，不等于 APK 文件数。'% (apk['targets'],apk['unique_packages'])]
    if history:
        counts = history.get('status_counts', {})
        lines += ['', '### 历史目标逐项核查', '',
                  '原 %s 条历史记录涉及 %s 个官方项目，已逐项读取当前与归档范围，结果如下：'%(history['baseline_targets'],history['programs_queried']), '',
                  '| 结论 | 条目数 |', '| --- | ---: |']
        for key,label in [('in_scope','官方仍列入范围'),('archived','官方已归档'),('out_of_scope','官方明确范围外'),('not_android','官方当前条目为网页 / iOS'),('android_unresolved','范围有记录，Android 对应待核'),('not_listed','当前完整范围未列出'),('unavailable','官方来源不可读')]:
            if counts.get(key):
                lines.append('| %s | %s |'%(label,counts[key]))
        lines += ['', '[逐项核查证据与时间](../赏金APK/history-review.json) · [在看板查看全部历史核查结果](https://8eeth0ven.github.io/security-md-collect/赏金APK/赏金APK看板.html?bounty=all&scope=reviewed)', '',
                  '“仍列入范围”不代表当前可投递：项目暂停 / disabled 另行标注并移出默认赏金结果。网页 / iOS 条目表示本次官方条目没有确认 Android，不能据此断言同名应用不存在。范围外和归档记录保留用于追溯。名称型、混合移动范围及商店特殊入口仍可能需要补包名证据。']
    lines += ['', '- YesWeHack 直读官方公开分页及详情；其他三个平台本轮对照 [bounty-targets-data](https://github.com/arkadiyt/bounty-targets-data) 的固定提交。提交、哈希、官方详情 URL 与原始 Android 范围计数见 [coverage.json](../赏金APK/coverage.json)。',
              '- Intigriti 来源仅含上游可访问的公开、开放、无需 TAC / 2FA 项目；登录范围未覆盖。HackerOne 兼容 `GOOGLE_PLAY_APP_ID` 与 `OTHER_APK`。',
              '- 历史记录只有读取完整官方范围后才更新结论；归档与明确范围外分别记录，不将快照缺失等同移除。同一 Play URL 的语言参数归并，原始来源行另存 [source-observations.json](../赏金APK/source-observations.json)。',
              '- 包名只从明确 Android 范围值、Play URL 或该 Android 目标内明确标注的 App Link 提取；通用描述、排除列表不抽取。人工旧映射保持待核标签。',
              '- 泛开发者页、搜索页、SDK、硬件、名称型范围不能自动变成唯一包名。单目标无赏金不会因项目有奖金就变成有赏金。APKPure 仅生成候选入口，没有下载验证。', '',
              '## 国内 SRC', '',
              '国内 SRC 目录现有 %s 条目标记录，其中 %s 条暂停；另有 %s 条独立国外官方计划记录，单列为 official，不混入国内 SRC。Android 身份与当前或历史官方范围分别取证，候选仍保留在发现与待核目录。'%(domestic_summary['records'],domestic_summary['paused_records'],len(official_records)), '',
              '[打开国内 SRC 清单](https://8eeth0ven.github.io/security-md-collect/赏金APK/赏金APK看板.html?platform=src&bounty=all) · [逐条证据](../赏金APK/src-evidence.json) · [来源校验清单](../赏金APK/src-sources.json)', '',
              '- 范围与安装入口分别取证；安全币可兑现金的条件保留在每条记录中，小米未确认当前奖金规则时标待确认。',
              '- 官方 APK 的 HEAD 200 仅证明当次响应；没有下载整包、验证包名、签名或内容完整性。商店维护和旧版本状态另行提示。',
              '- 腾讯旧6条保留 YesWeHack 官方渠道来源；本轮另有30条通过当前腾讯公开文档具名或其他移动客户端范围及独立发布者证据入库。尚未逐App读完当前暂停名单的条目标提交状态 unknown，不能把范围关联当作当前开放。',
              '- 暂停接收也保留已确认的当前或历史范围，标 paused / closed 并排除当前可投与赏金筛选；历史奖励说明不保证当前资格。vivo 已补具名Android范围并保留暂停状态，其他系统应用仍需逐包证据。',
              '- 顺丰3条使用官方搜索索引中的历史规则及独立Android身份，标间接历史证据；当前直开为停服公告，未证明该历史版本一直有效到暂停前。索引摘录与当前停服页的哈希分别保存。',
              '- 四平台、独立官方计划和国内SRC可能出现同一应用；目标记录数不是唯一应用数，也不是已下载APK数。', '',
              '## 复现与继续更新', '', '```powershell',
              'python 脚本/update_apk_sources.py --official-ywh --cache-dir /path/to/pinned-source-json',
              'python 脚本/expand_policy_sources.py --source-dir /path/to/pinned-source-json --budget 900',
              'python 脚本/verify_apk_history.py --cache-dir /path/to/official-review-cache',
              'python 脚本/import_domestic_apk.py --evidence /path/to/reviewed-evidence.json --source-manifest /path/to/source-manifest.json',
              'python 脚本/build_dashboard.py',
              'python 脚本/audit_coverage.py --collector /path/to/local-collector', '```', '',
              'APK 更新命令只取公开元数据，全部抓取成功后才写快照；失败不会清空旧记录。每次更新应重建覆盖报告。策略补采与原定时采集共用独占锁。APK 源未加入无人值守调度，不能把手动更新说成持续实时同步。', '',
              '相关采集、增量合并与来源审计均有成熟先例，本轮不作原创声明。完整机器报告见 [索引/coverage.json](../索引/coverage.json)。', '']
    if scope_review:
        lines += ['## 原290候选逐项核查', '',
                  '原候选 %s 条已各有一条结果：范围确认 %s 条（当前范围关联 %s、暂停历史范围 %s），错归厂商 %s 条，官方明确排除 %s 条，仍待补证 %s 条。当前范围关联仍需另看提交状态，不等于当前可投。'%(review_summary['reviewed_candidates'],review_confirmed,review_counts['confirmed_scope'],review_counts['confirmed_paused'],review_misattributed,review_excluded,review_pending), '',
                  '[scope-review.json](../赏金APK/scope-review.json) 的 rows 保留原始批次逐条结论，additional_reviews 单列新增候选。每条记录包含Android身份、官方范围检查、时间、来源元数据与未决原因；完成核查可以得到确认、错归、排除或未决，不把“已处理”写成“全部确认”。', '']
    if discovery:
        apps = discovery.get('apps', [])
        pending_apps = sum(r.get('scope_status') == 'unverified' for r in apps)
        source_rows = {r.get('source'): r for r in app_source_coverage.get('sources', [])}
        baidu = source_rows.get('百度手机助手', {})
        myapp = app_source_coverage.get('source_status', {}).get('myapp', {})
        appchina = app_source_coverage.get('source_status', {}).get('appchina', {})
        lines += ['## 厂商应用发现与来源覆盖', '',
                  '- 逐厂商队列 %s 个，发现目录 %s 条，全部发现中仍待补范围证据 %s 条；与原290批次的待补证数量分别计数。'%(len(discovery.get('vendors',[])),len(apps),pending_apps),
                  '- 百度手机助手 %s 个关键词均按真实 pn / hasNextPage 翻到终止：%s 次成功查询页观察、%s 个唯一成功页面URL。缓存复用和同页被多个查询记录可产生差异，这两个数均不是物理HTTP请求总数。'%(baidu.get('exhausted_queries',0),baidu.get('successful_page_observations',0),baidu.get('unique_successful_page_urls',0)),
                  '- 腾讯应用宝完成 %s 个开发者全称查询，HTTP失败 %s；观察到的 SearchList 组件无应用分页，按 non_paginated 记录，不能据此声称列出该厂商全部应用。'%(myapp.get('publisher_name_queries',0),myapp.get('publisher_queries_http_failures',0)),
                  '- AppChina 遭遇429限流，来源状态 %s；保留未完成游标及实际尝试标记，没有把未请求的队列算成已穷尽。七麦公开接口受限，逐厂商七麦查询仍为0；失败或零命中不证明厂商没有应用。'%appchina.get('source_status','unknown'),
                  '- [app-source-coverage.json](../赏金APK/app-source-coverage.json) 的 checks 保存来源、关键词、分页游标、观察时间、响应哈希、缓存/实际网络尝试和终止原因；sources 与 source_status 汇总各来源的完成方式及限制。搜索结果穷尽只说明该次可见查询已结束，不代表厂商产品全集。',
                  '- 详情必须以请求对应的主App记录核对包名与开发者，推荐区不作为该App身份。商店归属线索不自动证明集团关系、SRC范围、当前接收或现金资格。',
                  '- [逐厂商状态和应用来源](../赏金APK/vendor-app-discovery.json) · [可搜索的发现目录](https://8eeth0ven.github.io/security-md-collect/赏金APK/赏金APK看板.html#app-discovery)', '']
    write(base/'docs/coverage.md', '\n'.join(lines))
    return policy


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--collector',type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.base.resolve(),args.collector),ensure_ascii=False))
