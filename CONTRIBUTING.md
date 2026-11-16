# 参与维护

欢迎补充厂商映射、修复失效索引、改进收集器与看板。请在 PR 中说明数据来源、修改原因和验证结果。

## 补充厂商

不要直接编辑自动生成的 `资产/vendors.json`。在 `资产/` 中新增 `厂商映射-自加.json`（或其他 `厂商映射-*.json` 文件）：

```json
[
  {
    "vendor": "Example",
    "src": "官方披露计划名称或无",
    "orgs": ["example-org"],
    "unverified": [],
    "note": "官方组织归属与计划页面链接"
  }
]
```

确认组织属于该厂商，提供官方链接。组织归属按映射文件顺序合并，同一组织仅归一个厂商。现有四份基础映射优先，自定义映射按文件名排序追加。`src` 是来源描述，不是赏金资格或测试授权。

## 补充 Android 与 SRC 记录

Android身份和官方计划范围需要两份独立证据：详情页中明确的包名、产品名和发布者，以及可读的官方当前或历史范围。商店名称、品牌词、开发者搜索命中和域名范围不能单独推导原生App范围；同名但不属该厂商的记录应纠正归属。只取主App详情，不能把推荐区的另一个产品当成所请求的App。

暂停接收的计划仍可收录已确认的Android身份与历史范围，同时记录 `program_state=paused`、`submission_state=closed` 和暂停公告来源。历史现金规则不能显示为当前赏金资格；未读到当前接收规则时保留 `unknown`。搜索索引中的历史政策与当前页面证据分开记录，不把索引摘录哈希冒充当前政策原文哈希。源日期和整理日期分别保留。

- `赏金APK/scope-review.json` 的 `rows` 对应固定原始候选批次，一条候选一条结论；`additional_reviews` 记录新发现，不能用新增项替代原批次的未决项。范围确认、历史暂停、错归、明确排除与待补证分别计数。
- `赏金APK/app-source-coverage.json` 记录每次查询的分页游标、响应哈希、观察时间、缓存/实际网络尝试及终止原因。按真实 `hasNextPage` 或末页信号遍历；达到限额、超时、429、重复页或来源不可访问时保留未完成状态。页面没有分页组件时记 `non_paginated`，不伪造下一页，也不声称该厂商应用全集已收齐。
- 查询页观察次数、唯一URL数和物理HTTP请求数分别统计。没有完整请求日志就保留请求数未知；排队但因限流未发出的查询不能计为已尝试或已穷尽。

国内SRC写入 `src_android.json`；独立国外官方计划写入 `official_android.json`，保留官方计划来源。四个平台、国内SRC和独立官方计划可能指向同一包名，记录数不能当作唯一应用数。私有响应缓存放在发布目录外，发布账本不得携带凭据、瞬态CSRF参数或本机路径。

## 修改代码

需要 Python 3.10+；前端使用原生 HTML / CSS / JavaScript，无 Node 构建步骤。

```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python 脚本/build_dashboard.py
python 脚本/serve.py
```

前端源文件为 `脚本/dashboard.html` 和 `web/`，根 `index.html`、`索引/dashboard.json` 由生成器输出。修改模板后重新生成，避免下轮采集覆盖手工修改。

浏览器回归测试：

```bash
python -m playwright install chromium
python tests/browser_checks.py
python tests/apk_browser_checks.py
```

测试仅使用本地快照，不调用收集器、不扫描外部目标。检查手机宽度、中英文切换、空结果、分页、排序、数据加载失败，以及 `/security-md-collect/` 子路径的链接。新增行为请补对应的回归用例。

## 提交与数据

- 修改说明与截图应反映真实行为；大规模采集与视觉修改分别提交。
- 不提交 token、运行状态、组织缓存、日志或本机路径。
- 引用策略请保留来源。修正数据时说明具体厂商、仓库、上游路径及复现方式。
- 项目没有内置定时调度。已有外部同步应使用 `sync_github.py`；默认仅更新本地数据，显式 `--push` 才提交推送，禁止从数据目录覆盖应用代码。
