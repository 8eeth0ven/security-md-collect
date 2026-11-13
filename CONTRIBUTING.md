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
