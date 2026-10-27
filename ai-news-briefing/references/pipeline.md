# 流程细节

## 0. 创建工程

```bash
python scripts/new_project.py --dir ../ai_brief --fonts-dir ../hf_news/assets/fonts
cd ../ai_brief
```

生成结构：

```
ai_brief/
├── build.py                # 配音 → 时间轴 → 混音 → index.html
├── template.tpl            # HyperFrames 模板（4K、双层进度条、擦除转场、来源截图面板）
├── package.json            # npx hyperframes@0.8.197
├── content.example.json    # 8 条完整示例
├── scripts/
│   ├── collect_daily.py    # 多源采集与候选排序
│   ├── capture_evidence.py # 原文截图与正文导出
│   ├── make_covers.py      # 16:9 / 4:3 横版封面
│   └── tts_provider.py     # Qwen3-TTS / 火山
├── assets/
│   ├── fonts/              # NotoSansSC-VF.ttf / NotoSerifSC-VF.ttf
│   ├── vendor/gsap.min.js
│   ├── audio/raw|vo|mix
│   └── evidence/           # 截图 + manifest.json
└── out/                    # 候选清单、抽帧、成片
```

## 1. 采集候选

```bash
python scripts/collect_daily.py --top 20 --recommend 8
```

- 默认远端拉取：ai-news-radar（GitHub raw）、AI HOT selected、follow-builders feed、OpenAI/DeepMind RSS。
- `--offline` 只读工作区 `oss/` 下的本地克隆；`--no-rss` 跳过官方 RSS。
- 输出：`out/daily/candidates-<date>.json` 与同名 `.md`。
- 字段：`title / url / source / source_kind / published_at / summary / vendor / news_type / confidence / score / alt_sources`。
- 采集器已内置：相邻重复合并、周报/日报/观点文降权、官方域名加信、X 单源标注。

门槛：候选池 ≥ 100；`recommended` 里至少 2 条官方确认；`confidence` 分布要有 `官方确认` 或 `多源印证`。

## 2. 选稿与写截图计划

从 `recommended` 里选 6–10 条。每条都要有能打开的原文页；官方页打不开时，用 IT之家、界面新闻、36氪、ITBear 等媒体报道替代，并保留官方链接在旁白来源里。

写 `assets/evidence/evidence_plan.json`：

```json
{
  "items": [
    {
      "id": "anthropic_ipo",
      "url": "https://www.anthropic.com/news/s1-sec",
      "label": "官方公告",
      "source": "anthropic.com",
      "position": "center center",
      "fit": "cover"
    }
  ]
}
```

- `id`：同时用作截图文件名与 content.json 的 story id。
- `label`：`官方公告` / `官方博客` / `官方研究` / `媒体报道` / `技术博客`。
- `position`：`object-position`，如 `top center`、`center 85%`、`center center`。页面顶部留白多时，用 `center 80%–100%` 把正文移到面板里。
- `fit`：`cover`（默认，铺满）或 `contain`（正文很长很宽时完整显示）。

## 3. 抓证据截图

```bash
python scripts/capture_evidence.py --plan assets/evidence/evidence_plan.json
```

- 输出：`assets/evidence/<id>.png`、`assets/evidence/manifest.json`、`out/evidence_text/<id>.txt`。
- 每张图 2160×1350（1440×900 @1.5x），并记录 `final_url / title / h1 / text_excerpt / captured_at`。
- 失败项会在 stdout 标 `[err]`；换 URL 或换来源后重跑，不要用空图。
- 抓完必须打开截图看一遍：标题或正文要能看清，不能只有导航和空白。

## 4. 写 content.json

结构见 `references/content-schema.md`。硬要求：

- `narration` 只写截图正文/候选摘要里有的事实，1–2 句，约 25–50 字。
- 每条 story 2 张卡片（内容少时 `single: true` + 1 张），`body` 约 30–60 字。
- `source` 写 `来源 · 域名 · 原文 <日期>`；`evidence.captured` 写 `截取 <日期>`。
- `nav` 只放实际用到的类型；底部进度条按 `nav.w` 分配宽度。
- 封面 `index` 条数 = story 条数；`meta` 写 `["<date>", "公开信息整理", "<N> 条要闻"]`。

## 5. 构建

```bash
python build.py --speed 1.68             # 首次会生成全部 raw_*.wav
python build.py --reuse-tts --reuse-master --speed 1.68   # 改文案/改布局时复用配音
```

- GPU 可用时 `tts_provider.synthesize_qwen` 自动 `device_map="cuda"`；CPU 生成很慢，不建议。
- 输出：`index.html`、`assets/audio/mix.wav`、`assets/audio/timeline.json`。
- 构建结束自动调用 `scripts/make_covers.py`，生成 `out/covers/cover_16x9.png|jpg` 与 `cover_4x3.png|jpg`；`--no-covers` 可跳过。
- 时长、切换点、点击点由每条 `vo_*.wav` 实际时长计算；不设 30 秒上限。

## 6. 封面

封面不是截视频帧，而是读 `content.json` 的封面标题、副标题、索引、日期和厂家重新排版：

- 16:9：1920×1080，用于 B 站等横版平台；JPG < 5MB，满足 B 站 ≥1146×717 的要求。
- 4:3：1440×1080，用于公众号、小红书、站内推荐等位置。
- 两张都输出 PNG（无损）和 JPG（上传用）。
- 大标题优先读 `cover.headline`，没有就回退 `cover.title`；钩子必须基于事实，不能编造数字。
- 其余文案来源：`cover.subtitle / caption / index / meta`；索引 16:9 显示前 4 条，4:3 显示全部（最多 8 条）。
- 字体缺失会显示方框；确保 `assets/fonts/NotoSansSC-VF.ttf` 和 `NotoSerifSC-VF.ttf` 存在。
- 标题太长时改 `make_covers.py` 里的 `.title` 字号/`max-width`，或缩短 `cover.title`。

## 7. 渲染与验收

```bash
export PATH="<ffmpeg-dir>:$PATH"
npx --yes hyperframes@0.8.197 check
npx --yes hyperframes@0.8.197 snapshot --at 2,9,20,49,57.5 --output out/snap --no-end
npx --yes hyperframes@0.8.197 render --quality high --output out/ai_brief_4k.mp4
python ../ai-news-briefing/scripts/verify_render.py out/ai_brief_4k.mp4
```

门槛：

- `check`：0 error；Layout 0 error；Motion 0 error。`text_below_floor`、`line_unread` 是建议项，能改文案就改，改不动不阻塞。
- 抽帧：封面索引完整；每条右侧来源截图能看到标题/正文/域名/截取日期；底栏厂家名称不溢出。
- ffprobe：3840×2160、30fps、H.264 + AAC 48k。
- 点击音：`verify_render.py` 输出每个切换点 `peak`；正常应 ≥ 0.10，静音段约 0.003。
- 尾屏：在最后一个切换点 +0.5s 之后抽帧（内容入场从 `ts+0.5` 开始）。
- 封面：`cover_16x9` 1920×1080、`cover_4x3` 1440×1080；两张都要打开看，标题不能溢出、不能压住索引。