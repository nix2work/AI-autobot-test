# AI×UX Daily Digest → 飞书群机器人（Webhook）

每天北京时间 **09:00** 自动抓取 AI×UX 资讯（中英混合），生成 Digest，并通过 **飞书群自定义机器人 Webhook** 推送到群聊。

## 你需要准备什么

### 1) 飞书群自定义机器人 Webhook
- 在目标群里：群设置 → 群机器人 → 添加机器人 → 自定义机器人
- 拿到 **Webhook URL**
- 如果你开启了安全策略：
  - **签名校验（密钥）**：记录密钥（可选）
  - **关键词**：记录关键词（可选）

### 2) GitHub Repo Secrets（必须在 GitHub 仓库里配置）

- `FEISHU_WEBHOOK_URL`：必填，飞书机器人 webhook
- `FEISHU_SECRET`：可选，签名密钥（如果你开启了“签名校验”）
- `FEISHU_KEYWORD`：可选，关键词（如果你开启了“关键词”安全策略）
- `SOURCES_JSON`：可选，自定义 RSS 源（JSON 字符串，覆盖默认源）

## 本地运行（用于验证）

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 必填
export FEISHU_WEBHOOK_URL='https://open.feishu.cn/open-apis/bot/v2/hook/xxxx'

# 可选
export FEISHU_SECRET=''
export FEISHU_KEYWORD=''

python -m bot.run
```

运行后会：
- 抓取 RSS → 过滤/排序 → 去重 → 生成飞书 `post` 富文本 → 推送到群
- 更新 `state/seen.json`

## GitHub Actions（定时 09:00 CST）

工作流文件：`.github/workflows/digest.yml`

- 定时：`cron: 0 1 * * *`（UTC 01:00 = 北京时间 09:00）
- 支持手动触发：workflow_dispatch
- 默认会尝试把更新后的 `state/seen.json` **commit 回仓库**（这样去重才能跨天生效）

如果你不希望自动提交 state，可以在 workflow 里注释掉 “Commit state” 这一步，或改用外部存储（gist/kv）。

## 自定义资讯源（可选）

你可以在 GitHub Secrets 里设置 `SOURCES_JSON`，格式示例：

```json
{
  "ai": [
    {"name": "OpenAI", "url": "https://openai.com/blog/rss/"}
  ],
  "ux": [
    {"name": "NNg", "url": "https://www.nngroup.com/feed/rss/"}
  ],
  "product": [
    {"name": "Figma", "url": "https://www.figma.com/blog/rss/"}
  ]
}
```

