# ai-news-briefing

把每日 AI 资讯做成一支带**原文截图**的 4K 新闻视频。这是一个可在 Qoder / Claude Code 等支持 SKILL.md 的智能体里运行的技能包。

![预览](docs/preview-cover.jpg)

## 它做什么

1. **采集候选**：合并 ai-news-radar、AI HOT、follow-builders 与 OpenAI / DeepMind 官方 RSS，去重、打分、标注可信度。
2. **选稿与抓证据**：为每条新闻抓取原文页面截图，官方页打不开时使用可截图的媒体报道并标注来源类型。
3. **写稿**：生成中文旁白、卡片文案、封面索引和 `content.json`（事实只来自截图正文与候选摘要）。
4. **配音与合成**：本地 Qwen3-TTS（GPU 可用时自动 CUDA）或火山 TTS；生成双层进度条、点击音、擦除转场。
5. **渲染**：HyperFrames 渲染 4K MP4，时长由内容决定，**不设 30 秒上限**。
6. **验收**：HyperFrames `check` + 抽帧 + ffprobe + 切换点点击音检查。

## 仓库结构

```text
.
├── ai-news-briefing/          # 技能包（复制到 skills 目录即可用）
│   ├── SKILL.md
│   ├── scripts/               # new_project.py / verify_render.py
│   ├── references/            # 流程、content schema、故障排查、信息源策略
│   └── scaffold/              # 工程脚手架：build.py、template.tpl、采集/截图/TTS 脚本
├── docs/preview-cover.jpg
├── LICENSE
└── README.md
```

## 安装

Qoder（用户级）：

```bash
git clone https://github.com/Wan-1230/ai-news-briefing.git
cp -r ai-news-briefing/ai-news-briefing ~/.qoder-cn/skills/
```

项目级：把 `ai-news-briefing/` 复制到项目的 `.qoder/skills/`。

安装后在对话里说“生成今天的 AI 早报视频”，或调用 `/ai-news-briefing`。

## 依赖

- Python 3.12：`numpy`、`soundfile`、`playwright`（含 Chromium）
- Node 18+：`npx --yes hyperframes@0.8.197`
- FFmpeg / ffprobe：加入 PATH，或设置 `FFMPEG_BIN` / `FFPROBE_BIN`
- 字体：`NotoSansSC-VF.ttf`、`NotoSerifSC-VF.ttf`（Noto Sans/Serif SC 可变字体，仓库不打包）
- 语音（二选一）：
  - 本地 Qwen3-TTS：`AI_BRIEFING_TTS_MODEL` 指向模型目录
  - 火山 TTS：`VOLC_TTS_APPID` / `VOLC_TTS_TOKEN` / `VOLC_TTS_VOICE_TYPE`

## 快速开始

```bash
python ai-news-briefing/scripts/new_project.py --dir ./ai_brief --fonts-dir ./fonts
cd ai_brief
python scripts/collect_daily.py --top 20 --recommend 8
# 写 assets/evidence/evidence_plan.json（字段见 references/pipeline.md）
python scripts/capture_evidence.py --plan assets/evidence/evidence_plan.json
# 写 content.json（schema 见 references/content-schema.md）
python build.py --speed 1.68
export PATH="<ffmpeg-dir>:$PATH"
npx --yes hyperframes@0.8.197 check
npx --yes hyperframes@0.8.197 render --quality high --output out/ai_brief_4k.mp4
python ai-news-briefing/scripts/verify_render.py out/ai_brief_4k.mp4
```

## 已验证

- 脚手架工程 `hyperframes check`：**Check passed**，Lint 0 error、Layout 0 error、Motion 0 error。
- 实测成片：3840×2160 / 30fps / H.264 + AAC 48k / 58.434s，9 个切换点点击音峰值 ≈ 0.475，静音段 0.003。
- 采集实测：单日 200+ 条候选，去重后 227 条，官方/多源/单源三档可信度标注。

## 第三方与版权

- 仓库内置 `gsap.min.js`，版权归 GreenSock/Webflow，遵循其 Standard License。
- Noto 字体、Qwen3-TTS 模型、HyperFrames 均不随仓库分发，需自行安装（各遵循其原始许可）。
- 生成视频里的新闻截图版权归原站点所有；公开发布前请自行确认使用授权，并保留来源标注。

## License

MIT