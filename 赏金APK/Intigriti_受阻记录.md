# Intigriti 受阻记录（2026-11-13）

## 已打通的公开数据面

1. **项目全量列表**：Algolia 索引 `programs_prod`（凭据来自 www.intigriti.com 前端 JS bundle：AppID `AAZUKSYAR4` / SearchKey `70d8a3400477311f27ce002ec953aeb0`）。POST `https://aazuksyar4-dsn.algolia.net/1/indexes/programs_prod/query`，**必须带 `Referer: https://www.intigriti.com/`**（否则 403 "Method not allowed with this referer"），HTTP 200，nbHits=195 全量落盘 `intigriti_raw/programs_all.json`。
2. **匿名 preview 详情**：GET `https://app.intigriti.com/api/core/public/programs/{companyHandle}/{handle}/preview` → HTTP 200 JSON（短描述+赏金表+programId），182/195 成功，落盘 `intigriti_raw/previews/`。GET `.../routing` 亦 200（view 路由信息）。

## 受阻点：brief scope（目标清单，含 Android targets）

完整 brief 需研究者登录态。匿名 GET base 详情端点与各变体结果：

| 端点 | 结果 |
|---|---|
| `GET app.intigriti.com/api/core/public/programs/{c}/{h}` | 403 intigriti 品牌 HTML 权限页（"You actually don't have access to this page"，非 WAF 挑战） |
| `GET app.intigriti.com/api/core/public/programs/{programId}/share` | 403 同上 |
| `GET app.intigriti.com/api/core/public/programs/{c}/{h}/tac` | 403 同上 |
| `GET api.intigriti.com/external/researcher/v1/programs` | 401（研究者 API，需 Bearer token） |
| `GET api.intigriti.com/core/public/programs/{c}/{h}` | 404 |
| `GET api.intigriti.com/public/programs/{c}/{h}` | 404 |
| `GET api.intigriti.com/anonymous/v1/programs、/external/anonymous/v1/programs` | 404 |
| `GET api.intigriti.com/swagger、/swagger/v1/swagger.json、/swagger/v2/swagger.json、/external/swagger/v1/swagger.json` | 404（swagger 已下线） |
| `GET www.intigriti.com/researchers/bug-bounty-programs/{c}/{h}` | 404（Next.js 无 SEO 详情页，列表数据全在前端 Algolia 客户端） |
| `POST Algolia query 不带 Referer` | 403 "Method not allowed with this referer"（Referer 白名单已破解，见上） |

## preview 被平台拒绝的 13 个项目（403）

Aylo 系（brazzers-bbp / mydirtyhobby-bbp / nutaku-bbp / pornhub-bbp / probiller-bbp / trafficjunky-bbp）、belfius、colruyt×2、liveperson、sdworx、skodaauto/cariadvdp、telenet。清单落盘 `intigriti_raw/previews_denied.json`。

## 建议主线程浏览器补法

注册/登录研究者账号后：逐项目打开 `https://app.intigriti.com/programs/{companyHandle}/{handle}`，页面 brief 的 scope 表即 Android targets；或带登录 token 调 `api.intigriti.com/external/researcher/v1/programs` 系列拉结构化 scope（Swagger 下线，端点按 app JS bundle 内路径）。195 项目全量句柄已在 `intigriti_raw/programs_all.json`（字段 companyHandle/handle/programId/programType）。