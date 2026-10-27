# content.json 字段

```json
{
  "meta": {
    "brand": "AI 早报",
    "date": "2026-10-26",
    "issue": "10.26",
    "voice_target": "云晓辰-知性",
    "voice_provider": "qwen-local",
    "voice_speaker": "Serena",
    "voice_note": "音色替换说明"
  },
  "nav": [
    { "name": "要闻", "w": 24 },
    { "name": "模型发布", "w": 18 },
    { "name": "产品应用", "w": 20 },
    { "name": "开发生态", "w": 14 },
    { "name": "前沿与传闻", "w": 12 }
  ],
  "screens": []
}
```

## meta

| 字段 | 说明 |
|---|---|
| `date` / `issue` | 用于导航日期和封面角标；日期取系统时间，不猜 |
| `voice_provider` | `qwen-local` 或 `volcengine`；`build.py --provider` 可覆盖 |
| `voice_speaker` | Qwen 音色名，默认 `Serena` |
| `voice_note` | 音色缺口说明，会写进工程备注 |

## nav

只放实际用到的类型。`w` 是相对权重，决定顶部导航和底部类型条的宽度；相邻同类型的故事会自动合并成一个类型段。

## screens

数组顺序即上片顺序：`cover` → `story*` → `outro`。

### cover

| 字段 | 说明 |
|---|---|
| `id` | 必须是 `cover` |
| `kicker` | 左上角小字 |
| `title` / `subtitle` | 主标题、副标题 |
| `caption` | 底部字幕条 |
| `narration` | 开场旁白，通常 30–50 字 |
| `issueStamp` | 背景大号日期，如 `10.26` |
| `meta` | 封面信息行，如 `["2026-10-26", "公开信息整理", "8 条要闻"]` |
| `index` | 今日索引，每条 `{ "cat": "<类型>", "text": "<短标题>" }`，条数等于 story 数 |

### story

| 字段 | 说明 |
|---|---|
| `id` | 与截图文件名一致，如 `kimi_k31` |
| `nav` / `category` / `categoryColor` | 类型、类型名、类型色 |
| `vendor` / `vendorColor` | 厂家名、厂家色（底部厂家条和右侧竖排字用） |
| `kicker` | 如 `模型发布 · 03` |
| `title` / `subtitle` | 屏幕主标题、副标题 |
| `source` | `来源 · 域名 · 原文 <日期>` |
| `caption` | 底部字幕条 |
| `narration` | 旁白，1–2 句 |
| `cards` | 1–2 张卡片：`{ "icon": "...", "title": "...", "body": "..." }` |
| `single` | `true` 时只有一张卡片，单卡占满左侧 |
| `evidence` | 来源截图配置，见下 |

可用图标：`calendar` `refresh` `clock` `workflow` `cube` `layout` `monitor` `spark` `moon` `users`。

### evidence

```json
{
  "image": "assets/evidence/kimi_k31.png",
  "label": "官方博客",
  "source": "kimi.com",
  "captured": "截取 2026-10-27",
  "position": "center 85%",
  "fit": "cover",
  "alt": "Kimi K3.1 Pro 官方博客截图"
}
```

- `label`：`官方公告` / `官方博客` / `官方研究` / `媒体报道` / `技术博客`。
- `position`：CSS `object-position`；正文在页面下半部时用 `center 80%–100%`。
- `fit`：`cover` 铺满；正文很宽用 `contain` 完整显示。
- 没有 `evidence` 的故事屏会退回旧版布局（左侧卡片占满宽度）。

### outro

| 字段 | 说明 |
|---|---|
| `id` | 必须是 `outro` |
| `kicker` / `title` / `subtitle` / `caption` / `narration` | 同封面 |
| `issueStamp` | 背景日期 |
| `recap` | 收尾厂家胶囊：`[{ "name": "Kimi", "color": "#2B2B2B" }]`，建议去重 |

## 时间轴规则（由 build.py 自动生成）

- `LEAD_IN=0.85`、`VOICE_GAP=0.24`、`TRANSITION_WINDOW=0.56`、`TAIL_HOLD=2.00`。
- 每条旁白生成 `vo_<id>.wav` 后，按真实时长排切换点；点击音在切换点 `+0.02s`。
- 屏幕入场动画从切换点 `+0.5s` 开始；最后一个屏幕的内容在 `+0.5s` 后才可见，抽帧要避开刚切入的瞬间。