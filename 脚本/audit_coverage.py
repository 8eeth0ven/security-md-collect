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
    apk = build_apk_board(base)
    sources = load(base/'赏金APK/coverage.json', {})
    history = load(base/'赏金APK/history-review.json', {})
    report = {'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
              'security_md': policy, 'android': apk, 'android_sources': sources.get('platforms', []),
              'domestic_src': load(base/'赏金APK/src-backlog.json', {}),'history_review':{k:v for k,v in history.items() if k!='rows'},
              'verdict': 'Incomplete: measured source coverage, with explicit unresolved and inaccessible scope.'}
    write(base/'索引/coverage.json', json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    lines = ['# 采集覆盖审计', '', '这份索引尚未覆盖所有 GitHub 安全策略，也未覆盖所有 SRC / 赏金 Android 应用。以下数字有明确来源边界，不宣称全网覆盖率。', '',
             '审计时间：'+report['generated_at'], '', '## SECURITY.md', '',
             '- 映射厂商 %s 个、GitHub 账户 %s 个；策略仓库 %s 个，本地原文 %s 份。'%(len(vendors),len(owners),len(records),policy['local_documents']),
             '- 其中账户 `.github` 默认策略仓库 %s 个；只计一份文档，不按可能继承它的仓库数扩增。'%policy['default_policy_repositories']]
    if collector:
        lines += ['- 已知目录缓存 %s 个仓库，已检查 %s 个，尚未检查 %s 个。这个分母只是本机已经发现的仓库，不能当作 GitHub 的全部仓库。'%(policy['known_catalog_repositories'],policy['checked_in_known_catalog'],policy['never_checked_in_known_catalog'])]
        status = policy['historical_error_rechecks']
        lines += ['- 早前误收录的历史错误档案复核：找到策略 %s 条、确认无策略 %s 条、仍待复核 %s 条；原始档案保留以便追溯。'%(status.get('policy_found',0),status.get('confirmed_absent',0),status.get('unresolved',0))]
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
              '国内 SRC 已在同一看板单列筛选；已确认 Android 入口的目标入目录，产品更名、无当前 Android 入口等候选留在[待核清单](../赏金APK/src-backlog.json)，不充当已收集 APK。', '',
              '[打开国内 SRC 清单](https://8eeth0ven.github.io/security-md-collect/赏金APK/赏金APK看板.html?platform=src&bounty=all) · [逐条证据](../赏金APK/src-evidence.json) · [来源校验清单](../赏金APK/src-sources.json)', '',
              '- 范围与安装入口分别取证；安全币可兑现金的条件保留在每条记录中，小米未确认当前奖金规则时标待确认。',
              '- 官方 APK 的 HEAD 200 仅证明当次响应；没有下载整包、验证包名、签名或内容完整性。商店维护和旧版本状态另行提示。',
              '- 腾讯现行提交页已改链腾讯文档；本轮使用腾讯自己在 YesWeHack 发布的可读官方 Android 规则，并保留与 TSRC 的渠道关系。不能把旧失效 PDF 的搜索摘要当作当前规则。',
              '- 四平台和国内 SRC 可能出现同一应用；条目数不是唯一应用数。vivo 等系统 / 自有应用广义规则仍缺逐包范围，不扩增成 APK。', '',
              '## 复现与继续更新', '', '```powershell',
              'python 脚本/update_apk_sources.py --official-ywh --cache-dir /path/to/pinned-source-json',
              'python 脚本/expand_policy_sources.py --source-dir /path/to/pinned-source-json --budget 900',
              'python 脚本/verify_apk_history.py --cache-dir /path/to/official-review-cache',
              'python 脚本/import_domestic_apk.py --evidence /path/to/reviewed-evidence.json --source-manifest /path/to/source-manifest.json',
              'python 脚本/build_dashboard.py',
              'python 脚本/audit_coverage.py --collector /path/to/local-collector', '```', '',
              'APK 更新命令只取公开元数据，全部抓取成功后才写快照；失败不会清空旧记录。每次更新应重建覆盖报告。策略补采与原定时采集共用独占锁。APK 源未加入无人值守调度，不能把手动更新说成持续实时同步。', '',
              '相关采集、增量合并与来源审计均有成熟先例，本轮不作原创声明。完整机器报告见 [索引/coverage.json](../索引/coverage.json)。', '']
    write(base/'docs/coverage.md', '\n'.join(lines))
    return policy


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--collector',type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.base.resolve(),args.collector),ensure_ascii=False))
