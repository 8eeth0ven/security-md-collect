# Android APK 与赏金项目目录

[打开在线目录](https://8eeth0ven.github.io/security-md-collect/赏金APK/赏金APK看板.html) · [返回主页](../README.md) · [CSV](dashboard.csv) · [JSON](dashboard.json)

默认明亮，支持深色与跟随系统、中英文切换、平台/赏金/入口筛选和分页。首屏静态输出前 25 条有赏金记录，JavaScript 不可用时也能阅读。

> 快照整理时间：2026-11-13 12:29。这里只整理公开元数据，不下载 APK、不验证第三方下载地址。

| 平台 | 全部目标 | 有赏金目标 | 有应用入口 |
| --- | ---: | ---: | ---: |
| Bugcrowd | 132 | 107 | 126 |
| YesWeHack | 53 | 53 | 46 |
| HackerOne | 819 | 386 | 804 |
| Intigriti | 1 | 1 | 0 |

## 字段与边界

- 目标条目数与唯一应用数不同；同一个包名可能属于多个项目或目标。
- “有赏金”依据快照的明确字段；HackerOne 同时要求计划有赏金且目标符合赏金资格，归档/不接收记录单独标注。积分、VDP 和未知状态不会默认算作有赏金。
- Google Play 为应用商店入口；APKPure 为第三方镜像候选。生成候选 URL 不等于验证下载成功，`download_verified` 当前全部为 false。
- 包名来源分为 Play 链接提取、人工映射待核对和未标注；无包名时保留项目页入口。
- 快照不等于当前赏金范围，研究前核对项目官方页面。
- 原始四平台 JSON 与清单保留在本目录。运行 `python 脚本/build_apk_board.py` 可离线重建。
