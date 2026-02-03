# 🚀 AI×UX Daily Digest - 完整部署指南

## 📋 本次更新内容

### ✅ 已修复的问题
1. **时区问题** - 推送时间修正为北京时间 09:00
2. **数量问题** - 调整为每天 8 条（AI:4, UX:4）
3. **时效性** - 扩展到 7 天内，最新内容优先

### ✨ 新增功能
1. **AI 智能摘要** - 每条资讯自动生成一句话中文摘要
2. **中文翻译** - 标题和摘要自动翻译成中文
3. **关键词优化**:
   - AI 领域：重点关注 "vibe coding" 相关内容
   - UX 领域：检测著名 UX 专家（John Maeda, Don Norman 等）
4. **双 API 支持** - Gemini API 优先，BigModel API 备用

---

## 📦 需要部署的文件

### 新增文件：
1. **bot/ai_helper.py** - AI 摘要和翻译模块

### 需要替换的文件：
1. **bot/fetcher.py** → `fetcher_final.py`
2. **bot/feishu.py** → `feishu_final.py`
3. **bot/run.py** → `run_final.py`
4. **.github/workflows/digest.yml** → `digest_final.yml`
5. **requirements.txt** → `requirements_final.txt`（保持不变）

---

## 🔐 GitHub Secrets 配置

### 必须添加的新 Secrets：

进入：Settings → Secrets and variables → Actions → Secrets

#### 1. GEMINI_API_KEY

#### 2. BIGMODEL_API_KEY

### 已有的 Secrets（保持不变）：
- ✅ FEISHU_WEBHOOK_URL
- ✅ FEISHU_SECRET（可选）
- ✅ FEISHU_KEYWORD（可选）

---

## 📝 部署步骤

### Step 1: 添加新文件

#### 1.1 创建 bot/ai_helper.py

1. 进入 GitHub: `https://github.com/nix2work/AI-autobot-test`
2. 导航到 `bot` 文件夹
3. Add file → Create new file
4. 文件名: `ai_helper.py`
5. 复制粘贴 `ai_helper.py` 的内容
6. Commit: `Add AI summary and translation module`

---

### Step 2: 替换现有文件

#### 2.1 替换 bot/fetcher.py
1. 打开: `bot/fetcher.py`
2. 点击编辑 ✏️
3. 删除所有内容
4. 粘贴 `fetcher_final.py` 的内容
5. Commit: `Update: 7-day filter, vibe coding, UX experts detection`

#### 2.2 替换 bot/feishu.py
1. 打开: `bot/feishu.py`
2. 点击编辑 ✏️
3. 删除所有内容
4. 粘贴 `feishu_final.py` 的内容
5. Commit: `Update: Chinese summary support`

#### 2.3 替换 bot/run.py
1. 打开: `bot/run.py`
2. 点击编辑 ✏️
3. 删除所有内容
4. 粘贴 `run_final.py` 的内容
5. Commit: `Update: Integrate AI summary generation`

#### 2.4 替换 .github/workflows/digest.yml
1. 打开: `.github/workflows/digest.yml`
2. 点击编辑 ✏️
3. 删除所有内容
4. 粘贴 `digest_final.yml` 的内容
5. Commit: `Update: Add API keys, confirm Beijing time`

---

### Step 3: 配置 GitHub Secrets

1. Settings → Secrets and variables → Actions → Secrets
2. 点击 **New repository secret**
3. 添加以下两个 Secrets:

**GEMINI_API_KEY:**
```
Name: GEMINI_API_KEY
Secret: [你的 Gemini API Key]
```

**BIGMODEL_API_KEY:**
```
Name: BIGMODEL_API_KEY
Secret: [你的 BigModel API Key]
```

4. 保存

---

### Step 4: 测试运行

1. 进入 **Actions** 标签
2. 点击 **AIxUX Digest to Feishu**
3. 点击 **Run workflow**
4. 等待运行完成（约 1-2 分钟）

---

## 📊 预期效果

### 日志输出示例：
```
📡 抓取资讯源（共 9 个）...
✓ 抓取到 47 条资讯
🔍 智能排序和过滤...
  过滤后剩余 38 条（7天内）
  [AI] 选取 4 条
  [UX] 选取 4 条
✓ 排序后保留 8 条
✓ 去重后有 6 条新内容
📝 准备处理 6 条
🤖 开始生成摘要和翻译（共 6 条）...
  [1/6] 处理: Introducing vibe-based coding...
  [2/6] 处理: John Maeda on design systems...
  [3/6] 处理: GPT-5 Preview Release...
  [4/6] 处理: Usability Testing Best Practices...
  [5/6] 处理: Anthropic Claude Updates...
  [6/6] 处理: Interaction Design Trends...
✓ 摘要生成完成
📤 准备推送到飞书...
✓ 状态已保存
✅ 推送成功!
```

### 飞书消息示例：
```
━━━━━━━━━━━━━━━━━━━━━━
AI×UX Daily Digest · 2026-02-03

📰 今日精选 (AI × UX)

• [AI] 基于氛围的编程新范式 — OpenAI
  探讨 vibe coding 如何改变开发者工作流程

• [AI] Claude 3.5 多模态支持更新 — Anthropic
  详解 AI 辅助编程的最新突破

• [UX] John Maeda 谈设计系统的未来 — NNg
  著名 UX 专家分享设计与技术融合的见解

• [UX] 可用性测试最佳实践 2026 — UX Collective
  介绍基于 AI 的用户研究新方法

...
━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🎯 关键特性

### 1. 智能排序优先级
```
总分 = 关键词匹配(30%) + 时效性(50%) + 来源权重(20%)
     + vibe coding 加成(30%)
     + UX 专家加成(25%)
```

### 2. 时效性
- 保留 7 天内内容
- 24 小时内 = 1.0 分
- 72 小时内 = 0.7 分
- 7 天内 = 0.3 分

### 3. AI 处理流程
```
原文 → Gemini API 生成摘要+翻译
       ↓ (如果失败)
     BigModel API 生成摘要+翻译
       ↓ (如果都失败)
     使用原标题，空摘要
```

### 4. 关键词检测
- **AI**: "vibe coding", "vibe", "ai coding" 等
- **UX**: 检测专家名字（不区分大小写）

---

## 🐛 故障排查

### 问题 1: AI 生成失败
**现象**: 日志显示 "Gemini 失败，切换到 BigModel API"
**原因**: API Key 错误或额度用完
**解决**: 
1. 检查 GitHub Secrets 中的 API Key 是否正确
2. 验证 API Key 是否有效
3. 检查 API 额度

### 问题 2: 只返回 4 条
**现象**: 推送的消息少于 8 条
**原因**: 7 天内内容不足，或去重过滤太多
**解决**:
1. 查看日志中的 "过滤后剩余" 数量
2. 可以临时调整为 14 天: `timedelta(days=14)`
3. 或添加更多 RSS 源

### 问题 3: 时间不对
**现象**: 推送时间不是 09:00
**原因**: cron 表达式错误
**当前配置**: `'0 1 * * *'` = UTC 01:00 = 北京 09:00 ✅

---

## 📈 成本估算

### API 调用成本（每天）:
- Gemini API (Flash-Exp): 免费或极低成本
- BigModel API (GLM-4-Flash): 约 0.002 元/千 tokens

### 每天消耗:
- 8 条文章 × 2 次调用（摘要+翻译）
- 每次约 500 tokens
- **总计**: 约 8,000 tokens/天
- **月成本**: < 5 元

---

## ✅ 部署检查清单

```
☐ 1. 创建 bot/ai_helper.py
☐ 2. 替换 bot/fetcher.py
☐ 3. 替换 bot/feishu.py
☐ 4. 替换 bot/run.py
☐ 5. 替换 .github/workflows/digest.yml
☐ 6. 添加 GEMINI_API_KEY 到 Secrets
☐ 7. 添加 BIGMODEL_API_KEY 到 Secrets
☐ 8. 手动运行 Actions 测试
☐ 9. 检查飞书消息格式
☐ 10. 等待明天 9:00 自动运行
```

---

## 🎉 完成！

部署完成后，你将拥有：
- ✅ 每天北京时间 09:00 自动推送
- ✅ 8 条精选资讯（AI:4, UX:4）
- ✅ 智能中文摘要
- ✅ 关键词优先（vibe coding, UX 专家）
- ✅ 7 天内最新内容
- ✅ 自动去重

有任何问题，随时告诉我！🚀
