[简体中文](README.md) · [English](README.en.md)

# Open-source security policy index

Look up a repository or vendor to find its published `SECURITY.md`, reporting channel and disclosure policy. The Android directory links public program records to app identifiers and official sources.

![Light cover for the index of repository security policies and upstream reporting sources](docs/assets/cover.svg)

- Browse or download the policy index. [Online dashboard](https://8eeth0ven.github.io/security-md-collect/) · [CSV](索引/总表.csv) · [JSON](索引/dashboard.json)
- Check Android program scope and review dates. [Android directory](赏金APK/README.md)

Search covers every page and accepts multiple keywords and common Chinese / English aliases, such as `Alibaba fastjson`. Relax conflicting filters in one click, or search and expand a vendor to preview its projects before opening the full list.

[Priority project checks](索引/重点项目核查.json) record repository checks, policy sources, account defaults, missing standard files and retry states. [Vendor app discovery](https://8eeth0ven.github.io/security-md-collect/赏金APK/赏金APK看板.html#app-discovery) keeps store discoveries separate from confirmed official scope.

The 2026-11-16 snapshot includes 223 domestic SRC records (44 paused), 9 records from independent international official programs, and 379 discovered app records. Every candidate in the original batch of 290 has a review result: 146 scope confirmations (118 current scope associations and 28 paused historical scopes), 16 incorrect vendor associations, 2 explicit exclusions, and 126 still awaiting evidence. Across the entire discovery directory, 146 records still need scope evidence. Paused programs remain indexed; historical scope and reward terms do not establish current submission or reward eligibility. Submission status and unresolved evidence are shown separately.

The [scope review ledger](赏金APK/scope-review.json) preserves per-app evidence and decisions. The [source coverage ledger](赏金APK/app-source-coverage.json) records queries, pagination, cache observations and stopping reasons. All 365 Baidu keyword queries reached `hasNextPage=false`. All 182 Tencent MyApp publisher-name queries completed, but the observed component exposes no app pagination. AppChina remains incomplete after HTTP 429 responses; Qimai was not queried for every vendor. The two store sources verified 50 new Android identity associations; incorrect vendor associations were removed separately, so 50 is not the directory’s net increase. Exhausting a visible query does not establish a complete vendor app inventory.

To browse the bundled snapshot locally, run `python3 脚本/serve.py` from the repository root with Python 3.10 or later. Open the address printed in the terminal. Viewing the snapshot needs no GitHub token.

Snapshots may lag upstream. Check the program's current official policy for reporting terms, scope and reward eligibility. [Coverage audit](docs/coverage.md) · [Snapshot statistics](索引/统计.json) · [Maintenance guide](CONTRIBUTING.md)
