---
name: ai-news-briefing
description: 生成每日 AI 早报视频：聚合 ai-news-radar、AI HOT、follow-builders 与官方 RSS，抓取新闻原文截图作为可信参考，写入中文旁白与卡片，用 HyperFrames 渲染 4K 成片，自动生成 16:9/4:3 横版封面并验收。Use when the user asks for an AI 早报 / AI 日报视频 / 每日 AI 资讯成片 / daily AI briefing video, or wants to turn collected AI news into a rendered news video.
---

# AI 早报视频

## 总览

把「每日 AI 资讯 → 带原文截图的 4K 新闻视频」拆成 6 步：采集候选、选稿并抓来源截图、写 `content.json`、生成配音与 HTML、渲染、验收。成片时长由内容决定，不设 30 秒上限。

## 前置依赖

- Python 3.12：`numpy`、`soundfile`、`playwright`（含 Chromium）、`requests`；TTS 另需 `torch`、`qwen_tts`
- Node 18+：`npx --yes hyperframes@0.8.197`（check / snapshot / render）
- FFmpeg / ffprobe：设置 `FFMPEG_BIN` / `FFPROBE_BIN`，或把所在目录加入 PATH
- 字体：`NotoSansSC-VF.ttf`、`NotoSerifSC-VF.ttf` 放到工程 `assets/fonts/`
- 语音（二选一）：
  - 本地 Qwen3-TTS：`AI_BRIEFING_TTS_MODEL` 指向模型目录（GPU 可用时自动走 CUDA）
  - 火山 TTS：`VOLC_TTS_APPID` / `VOLC_TTS_TOKEN` / `VOLC_TTS_VOICE_TYPE`（云晓辰-知性的 voice_type 必须从控制台取）
- 截图浏览器：`AI_BRIEFING_CHROMIUM` 指向 `chrome.exe`（Playwright 缓存里的 Chromium 也可）

## 快速开始

```bash
python scripts/new_project.py --dir ../ai_brief --fonts-dir ../hf_news/assets/fonts
cd ../ai_brief
python scripts/collect_daily.py --top 20 --recommend 8
# 按 references/pipeline.md 写 assets/evidence/evidence_plan.json
python scripts/capture_evidence.py --plan assets/evidence/evidence_plan.json
# 按 references/content-schema.md 写 content.json
python build.py --speed 1.68
export PATH="<ffmpeg-dir>:$PATH"
npx --yes hyperframes@0.8.197 check
npx --yes hyperframes@0.8.197 snapshot --at 2,9,20,49,57.5 --output out/snap --no-end
npx --yes hyperframes@0.8.197 render --quality high --output out/ai_brief_4k.mp4
python ../ai-news-briefing/scripts/verify_render.py out/ai_brief_4k.mp4
# 可选：B 站发布（默认 dry-run，确认后加 --execute）
python scripts/publish_bilibili.py --project . --cookie <cookies.json> \
  --season-id <合集ID> --section-id <小节ID>
```

## 六步流程与门槛

1. **采集候选**：`python scripts/collect_daily.py --top 20 --recommend 8`。合并 ai-news-radar、AI HOT、follow-builders、OpenAI/DeepMind RSS，输出去重后的 `out/daily/candidates-<date>.json|md`。门槛：候选池 ≥ 100，推荐里至少 2 条官方确认。
2. **选稿**：从 `recommended` 里选 6–10 条。每条必须有可打开、可截图的原文页；优先官方公告、模型发布、产品更新；过滤周报/日报/观点文；不为时长删新闻。
3. **证据截图**：写 `assets/evidence/evidence_plan.json`（字段见 `references/pipeline.md`），运行 `capture_evidence.py`。每张图必须能看到标题或正文；官方页不可截时用 IT之家、界面新闻、36氪、ITBear 等媒体报道，`label` 写 `媒体报道`。
4. **写稿**：只使用截图正文和候选摘要里的事实；每条 1–2 句旁白、2 张卡片；写 `content.json`（schema 见 `references/content-schema.md`）；来源行写 `来源 · 域名 · 原文 <日期>`，截图脚注写 `截取 <日期>`。封面图按 `references/cover-design.md` 的骨架写：`cover.hook_lines`（1–3 行、每行 2–6 字）、`cover.subhook`（一行事实）、`cover.logos`（厂商 logo 墙）；钩子必须有事实支撑，不能编造数字。
5. **构建**：`python build.py --speed 1.68`；首次加 `--force-tts`，改文案但复用配音时用 `--reuse-tts --reuse-master`。输出 `index.html`、`assets/audio/mix.wav`、`assets/audio/timeline.json`，并自动生成 `out/covers/cover_16x9.png|jpg` 与 `cover_4x3.png|jpg`；加 `--no-covers` 可跳过。
6. **渲染与验收**：check → snapshot → render high → `verify_render.py`。门槛：check 0 error；快照里标题和来源截图看得清；ffprobe 确认 3840×2160 / 30fps / AAC 48k；点击音峰值 ≥ 0.10；两张封面尺寸正确（16:9 1920×1080，4:3 1440×1080）。
7. **B 站发布（可选）**：`python scripts/publish_bilibili.py --project . --cookie <cookies.json> --season-id <合集ID> --section-id <小节ID>` 先 dry-run；确认后加 `--execute`。脚本会上传视频、解析 BV，再 `biliup season add` 加入合集；`--skip-season` 可跳过合集。

## 硬规则

- 不编造事实、数字、日期；日期用系统时间现取。
- 官方一手源优先；X/社交/公众号默认单源，必须再有第二个来源才能进「要闻」。
- 证据标签分三档：官方公告/官方博客/官方研究、媒体报道、技术博客；媒体源不允许写成官方。
- 成片不设 30 秒上限，条数由内容价值决定。
- 封面从 `content.json` 生成，不截视频帧；16:9 用于 B 站等横版平台，4:3 用于公众号/其他位置。
- 封面只放“超大钩子 + 厂商标识 + 一行副钩子”，不要放 8 条索引小字；缩略图尺寸下先读大字。
- B 站发布默认只做 dry-run；`cookies.json` 不进仓库，用户明确说“发”才执行上传。
- 混音避免最终 `loudnorm` 截断时长，用定长 PCM + 峰值归一。
- 渲染前必须让 ffmpeg/ffprobe 在 PATH 或 `FFMPEG_BIN`/`FFPROBE_BIN` 中，否则 `render` 直接失败。

## 资源

- `scaffold/`：可复制的工程脚手架（`build.py`、`template.tpl`、采集/截图/TTS/封面/发布脚本、GSAP、示例 `content.json`、示例截图计划）
- `scripts/new_project.py`：创建工程、复制脚手架与字体
- `scripts/verify_render.py`：ffprobe 规格 + 切换点点击音检查
- `references/pipeline.md`：每步命令、字段与预期输出
- `references/content-schema.md`：`content.json` 全字段
- `references/cover-design.md`：封面版式、钩子公式、尺寸、logo 规则与自检清单
- `references/troubleshooting.md`：本机网络、Chromium、GPU TTS、FFmpeg 等已知坑
- `references/sources.md`：信息源、可信度分级与写稿红线
- `references/bilibili.md`：biliup 自动投稿方案（可选，默认 dry-run）