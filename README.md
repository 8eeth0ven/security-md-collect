# security-md-collect — 大厂开源项目 SECURITY.MD 收集库

自动收集**国内外大厂的开源项目**中**带有 SECURITY.md（安全策略/漏洞上报入口）的仓库**：GitHub 地址 + SECURITY.md 原文，按厂商分文件夹存放，每 30 分钟定时增量更新。另含 **赏金APK 分类**：四大漏洞赏金平台（Bugcrowd / YesWeHack / HackerOne / Intigriti）公开赏金项目的 Android APK 清单（包名 → APKPure 镜像直下链 + Play 官方页）。

## 这是什么

- **收录标准**：在 HackerOne / Bugcrowd / 国内主流 SRC（TSRC、ASRC、MSRC、JSRC、BSRC、HSRC、MiSRC、DSRC、360、B 站、快手、携程、蚂蚁等）有公开计划的一律收录；另含全球科技/云/安全大厂、头部 AI 公司与 Apache/CNCF 基金会。
- **数据**：243 个厂商 → 306 个 GitHub 组织，收录数千个含 SECURITY.md 的仓库（每仓库存 SECURITY.md 原文 + 星数/语言元数据）。
- **赏金APK**：Bugcrowd 全量 296 项目（132 APK / 115 直链）+ YesWeHack 52 项目（53 APK / 46 直链），H1 / Intigriti 抓取完成后自动纳入；直下链需代理，XAPK 用 APKPure 安装器解包。
- **本仓库内容**：收集器脚本（双模式：GitHub token code search / 无 token HTML 抓取）、厂商映射、收录清单快照、静态看板（`index.html`）。

## 内容分类

| 类别 | 位置 | 说明 |
|---|---|---|
| 【服务网站】 | `index.html`（本仓库根，GitHub Pages 可直开）+ `脚本/serve.py` | 静态看板：全部收录仓库可搜索、直达 GitHub 项目页 |
| 【本地文本】 | `厂商/{厂商}/`（清单.md、repos.json、各仓库 SECURITY.md 原文）、`索引/总表.csv`、`索引/统计.json` | 收录数据：含 星数/语言/许可/SECURITY.md 路径 元数据 |
| 【赏金APK】 | `赏金APK/`（赏金APK看板.html + 各平台清单.md + 源 JSON） | 四平台赏金项目 Android APK 直达清单，看板可按平台/直链筛选 |
| 【本地脚本】 | `脚本/collect.py`（收集器）、`serve.py`（局域网看板）、`sync_github.py`（同步推送本仓库） | 定时任务每次收集后调用 sync_github.py 实时 push |
| 【厂商映射】 | `资产/vendors*.json` | 厂商→GitHub 组织映射，新增 `资产/厂商映射-自加.json` 即扩展 |

## 目录结构

```
├─ index.html            静态看板（全部收录仓库可搜索，含 GitHub 链接）
├─ 厂商/{厂商名}/          每厂商：清单.md（人读）+ repos.json（机读）+ {owner}__{repo}/SECURITY.md
├─ 索引/总表.csv           全量清单（Excel 直接打开）
├─ 索引/统计.json          统计快照
├─ 资产/vendors*.json      厂商→GitHub组织 映射（可自行扩展：新增 资产/厂商映射-自加.json 即可）
├─ 赏金APK/               四平台赏金 APK 清单：赏金APK看板.html + {平台}清单.md + 源 JSON + README.md
└─ 脚本/collect.py serve.py sync_github.py config.json
```

## 运行收集器

```bash
pip install requests
# 数据目录（默认 ~/Desktop/大厂开源SECURITY_MD收集，可用环境变量 SECMD_BASE 覆盖）
export SECMD_BASE="/path/to/data"
python 脚本/collect.py            # 增量收集（--budget 秒数 控制单轮预算；--force 强制重扫组织列表）
python 脚本/serve.py              # 局域网看板（0.0.0.0:8899，/status 为统计 JSON）
```

- **有 GitHub token**（env `GH_TOKEN`/`GITHUB_TOKEN`，或写入 `资产/.gh_token`，只读公共仓库权限即可）：自动切 code search 模式，按 org 一次查完全部 SECURITY.md，快 10 倍以上。
- **无 token**：自动用 HTML 抓取仓库列表 + raw 探测（7 种大小写/目录变体），负结果缓存 30 天；国内网络环境建议配置本机代理并修改 `脚本/config.json`。
- 断点续跑 + 进程锁（`脚本/collect.lock`，2 小时锁），适合放进任意调度器每 30 分钟跑一次。

## 数据与隐私说明

- 收录数据全部来自 GitHub 公开信息（仓库名/星数/语言/SECURITY.md 原文）与公开的厂商→组织映射，不含任何凭据或本机信息。
- 运行时产物（state.json、日志、token 文件）已列入 `.gitignore`。
- SECURITY.md 版权归各仓库所有者，本库仅作安全研究索引用途。
