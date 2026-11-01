# 安全须知

agent 读取 `raw/` 里的素材，并据此写文件、改知识图谱、执行代码：

```
第三方网页 → 你保存进 raw/ → agent 读取全文 → agent 写 wiki/、改图谱、跑 run_python
```

素材正文和你的指令走同一条通道，藏在素材里的文字可能被当成指令执行。

## 四条建议

1. **只摄入你信任的来源。** `raw/` 不是收件箱，只放你决定让 agent 读的东西。
2. **把 `raw/` 的内容当不可信输入。** 新素材在对话里手动 Ingest，核对 agent 实际做了什么。定时任务只跑只读的 Lint，工具策略不授任何写工具。
3. **Agent access 按最小范围给。** 不需要 agent 读写整棵树时，只注册 `raw/`、`wiki/`。
4. **vault 里不放凭证和敏感个人数据。** 开了索引的文件夹会全文上传到你账号下的 Quick Space。

## 报告问题

安全问题请走 AWS 漏洞报告渠道：https://aws.amazon.com/security/vulnerability-reporting/ ，不要提交公开 issue。
