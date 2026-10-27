# B 站自动投稿（可选）

## 结论

可以自动化，但**不是 B 站官方对个人创作者开放的投稿 API**。可行路径是 [biliup](https://github.com/biliup/biliup)（5k+ star，Rust CLI）：支持登录、视频上传、封面、标题、分区、标签、转载声明和定时投稿。

## 前置

1. 下载 biliup Release 的 Windows 包（`biliupR-v*-x86_64-windows.zip`），解压后把 `biliup.exe` 放到 `tools/bin/` 或 PATH。
2. **一次性登录**（必须用户本人操作，Agent 不代跑交互式登录）：
   ```powershell
   biliup -u cookies.json login
   ```
   支持扫码 / 短信 / 账号密码 / 浏览器 Cookie；登录信息写入 `cookies.json`。
3. 确认命令参数：
   ```powershell
   biliup upload --help
   ```

## 推荐流程

```powershell
# 1) 先 dry-run，只打印参数，不投稿
biliup -u cookies.json upload out/hf_news_1026_4k.mp4 `
  --title "Anthropic 启动 IPO，AI 资本加速｜AI 早报 10.26" `
  --desc "8 条 AI 要闻，每条附原文截图。来源：..." `
  --tid 28 `
  --tag "AI,人工智能,Anthropic,OpenAI,Kimi" `
  --cover out/covers/cover_16x9.jpg `
  --copyright 1

# 2) 参数确认后真投（去掉 dry-run；具体 flag 以 upload --help 为准）
```

- 标题 ≤ 80 字，标签 ≤ 10 个。
- 封面只用 **16:9** 的 `cover_16x9.jpg`；4:3 给公众号/其他平台。
- 分区 `tid` 选错会影响推荐；AI 资讯通常选科技/数码相关分区，拿不准让用户确认。
- 定时投稿用 biliup 的定时参数（以 `upload --help` 为准）。

## 加入合集（必做）

上传成功后，用 BV 号把稿件加入“AI早报”合集的“正片”小节：

```powershell
# 1) 查自己的合集和小节 ID
biliup -u cookies.json season list

# 2) 上传成功后加入小节（<BV> 替换为上传返回的 BV 号）
biliup -u cookies.json season add --vid <BV> <SECTION_ID>

# 3) 确认小节里已有稿件
biliup -u cookies.json season sections <SEASON_ID>
```

- 合集 ID 和小节 ID 在 `season list` 输出里；每个账号不同，不要硬编码到公共脚本。
- 合集加入失败不影响稿件本身，但要在日志里明确记录，不能当成发布成功。
- 2026-10-28 实测：`biliup 1.3.4` 上传 4K 成片成功，随后 `season add` 加入“正片”小节成功；上传耗时 63.66s。

## 风险与边界

- B 站有上传风控，短时间频繁投稿可能返回 `601 上传视频过快`；不要批量并发。
- `cookies.json` 是账号凭证：只放本地，不提交 Git，不贴聊天记录。
- 社区接口可能随 B 站改版失效；biliup 需要保持更新。
- **默认不自动发布**：先生成封面、标题、简介、标签和 SRT，给用户 dry-run 预览；用户明确说“发”再执行上传。
- 目前 skill 只提供这份操作说明；`publish_bilibili.py` 包装脚本尚未加入。实际流程已跑通：Web 扫码登录 → `biliup upload` → `biliup season add`。

## 为什么不用官方开放平台

B 站开放平台主要面向企业/合作方，个人创作者没有通用的“一键投稿”公开 API。biliup 走的是网页端投稿接口，功能完整但不属于官方承诺接口，稳定性取决于 B 站页面。
