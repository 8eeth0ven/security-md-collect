# 采集覆盖审计

这份索引尚未覆盖所有 GitHub 安全策略，也未覆盖所有 SRC / 赏金 Android 应用。以下数字有明确来源边界，不宣称全网覆盖率。

审计时间：2026-11-14T05:06:59+00:00

## SECURITY.md

- 映射厂商 304 个、GitHub 账户 385 个；策略仓库 9869 个，本地原文 9869 份。
- 其中账户 `.github` 默认策略仓库 104 个；只计一份文档，不按可能继承它的仓库数扩增。
- 已知目录缓存 58497 个仓库，已检查 58497 个，尚未检查 0 个。这个分母只是本机已经发现的仓库，不能当作 GitHub 的全部仓库。
- 早前误收录的历史错误档案复核：找到策略 25 条、确认无策略 883 条、仍待复核 0 条；原始档案保留以便追溯。

已补账户默认策略与公开范围中明确列出的 GitHub 仓库；已有策略每 7 天、未发现策略每 30 天重查。错误不进入正/负缓存，策略确认为删除后移出当前索引。部分分页失败重试；代码搜索超过 1,000 或 `incomplete_results` 单列，不能宣称扫全。

[GitHub 官方继承规则](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file)规定 `.github/` → 根目录 → `docs/`，当前仓库没有时使用账户 `.github` 仓库的默认文件。未映射账户、动态改名、私有仓库、非标准文件名仍是缺口。

## Android 范围

| 来源 | 源项目数 | 原始 Android 范围行 | 合并后本轮观察记录 | 历史待复核 | 本轮无包名 |
| --- | ---: | ---: | ---: | ---: | ---: |
| bugcrowd | 296 | 130 | 128 | 30 | 28 |
| ywh | 52 | 45 | 45 | 9 | 3 |
| h1 | 450 | 544 | 532 | 299 | 10 |
| intigriti | 144 | 70 | 70 | 0 | 10 |

合并目录共 1113 条目标记录、987 个唯一有效格式包名；目标记录不等于应用数，不等于 APK 文件数。

- YesWeHack 直读官方公开分页及详情；其他三个平台本轮对照 [bounty-targets-data](https://github.com/arkadiyt/bounty-targets-data) 的固定提交。提交、哈希、官方详情 URL 与原始 Android 范围计数见 [coverage.json](../赏金APK/coverage.json)。
- Intigriti 来源仅含上游可访问的公开、开放、无需 TAC / 2FA 项目；登录范围未覆盖。HackerOne 兼容 `GOOGLE_PLAY_APP_ID` 与 `OTHER_APK`。
- 本轮不存在的旧目标保留为“历史快照·本轮未确认”，不自行判定出范围；同一 Play URL 的语言参数归并，原始行另存 [source-observations.json](../赏金APK/source-observations.json)。
- 包名只从明确 Android 范围值、Play URL 或该 Android 目标内明确标注的 App Link 提取；通用描述、排除列表不抽取。人工旧映射保持待核标签。
- 泛开发者页、搜索页、SDK、硬件、名称型范围不能自动变成唯一包名。单目标无赏金不会因项目有奖金就变成有赏金。APKPure 仅生成候选入口，没有下载验证。

## 国内 SRC

国内 SRC 尚未形成完整逐包库。保留独立的 [来源与产品待核清单](../赏金APK/src-backlog.json)，不会把厂商名称、产品官网或过期活动计成确认的有赏金 APK。

- [360 产品范围](https://src.360.cn/Product/product)与[奖励规则](https://src.360.cn/Reward/reward)可读；移动产品区单列名称和官方范围页，包名、维护状态和逐产品赏金资格待核。
- [vivo V2 规则](https://security.vivo.com.cn/assets/vivoSRC_process_2_0.pdf)可下载，属于系统 / 自有应用规则，尚无完整逐包范围。
- 腾讯旧 `TSRC.pdf` 地址本次 HTTP 404；规则的搜索索引不能替代可读正文。字节等动态范围、活动有效期和登录范围继续列缺口。

## 复现与继续更新

```powershell
python 脚本/update_apk_sources.py --official-ywh --cache-dir /path/to/pinned-source-json
python 脚本/expand_policy_sources.py --source-dir /path/to/pinned-source-json --budget 900
python 脚本/build_dashboard.py
python 脚本/audit_coverage.py --collector /path/to/local-collector
```

APK 更新命令只取公开元数据，全部抓取成功后才写快照；失败不会清空旧记录。每次更新应重建覆盖报告。策略补采与原定时采集共用独占锁。APK 源未加入无人值守调度，不能把手动更新说成持续实时同步。

相关采集、增量合并与来源审计均有成熟先例，本轮不作原创声明。完整机器报告见 [索引/coverage.json](../索引/coverage.json)。
