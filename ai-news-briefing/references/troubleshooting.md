# 常见故障

## 网络与抓取

| 现象 | 处理 |
|---|---|
| `urllib` 拉 900KB+ 的 GitHub raw 超时（40s+） | 用 `curl` 子进程抓取；本 skill 的 `collect_daily.py` 已改用 curl |
| `requests` 读 GitHub raw 超时，但浏览器能开 | 同上，curl 比 requests/urllib 稳定 |
| TechCrunch RSS 报 `CRYPT_E_REVOCATION_OFFLINE` | curl 加 `--ssl-no-revoke` |
| X / OpenAI 官网 / GitHub HTML / Product Hunt 打不开 | 换 IT之家、界面新闻、36氪、ITBear 等可访问媒体报道；来源标签改 `媒体报道` |
| HuggingFace 直连超时 | 用 AI HOT / ai-news-radar 里已有的模型发布条目，或厂商官方博客 |
| raw.githubusercontent 偶发 reset | curl 加 `--retry 3 --retry-delay 1`；失败回退本地 clone |

## Playwright 截图

| 现象 | 处理 |
|---|---|
| `Executable doesn't exist at ...chromium_headless_shell-1248` | 本机缓存版本和 Python 包不一致：`AI_BRIEFING_CHROMIUM` 指向已有 `chromium-<rev>/chrome-win64/chrome.exe` |
| 截图只有导航和空白 | 页面标题被滚动动画隐藏或留白过大：调整 `position`（`center 80%–100%`），或把截图裁到正文区域（PIL crop） |
| 登录弹窗遮住正文 | 截图脚本已注入 CSS 隐藏 cookie/login 弹层；不够时在计划里换来源 |
| 正文太长截不全 | 用 `fit: "contain"` 完整显示，或裁到标题+首段 |

## 配音

| 现象 | 处理 |
|---|---|
| CPU 生成 10 条要 10 分钟以上 | `tts_provider.synthesize_qwen` 会优先 `device_map="cuda"`；确认 `torch.cuda.is_available()` |
| 显存不足 | 关掉其它占显存进程；0.6B float32 约 4.3GB |
| 出现 `SoX could not be found` | Qwen TTS 的提示，不影响输出 |
| 想用云晓辰-知性 | 只有火山 TTS 路径：`VOLC_TTS_APPID` / `VOLC_TTS_TOKEN` / `VOLC_TTS_VOICE_TYPE`；voice_type 必须从控制台取，不能猜 |
| 改文案后配音没变 | `build.py` 默认复用已有 `raw_*.wav`；加 `--force-tts` 或删掉对应 raw 文件 |

## 封面

| 现象 | 处理 |
|---|---|
| 构建日志出现 `[covers] skipped` | Playwright 或 Chromium 不可用；设置 `AI_BRIEFING_CHROMIUM`，或单独跑 `python scripts/make_covers.py` |
| 封面中文变方框 | `assets/fonts/` 缺 Noto Sans SC / Noto Serif SC；用 `new_project.py --fonts-dir` 复制 |
| 标题溢出/压住索引 | 缩短 `cover.title`，或调 `make_covers.py` 的 `.title` 字号和 `max-width` |
| B 站上传封面失败 | 用 16:9 的 JPG（1920×1080），不要用 4:3；单张 < 5MB，格式 JPG/PNG |
| 4:3 版面太空 | 已默认列出全部 8 条索引；条目少时可调 `.portrait .layout` 的 `gap` 或增大字号 |

## 构建与渲染

| 现象 | 处理 |
|---|---|
| `render` 报 FFmpeg not found | `export PATH="<ffmpeg-dir>:$PATH"`，或设 `FFMPEG_BIN` / `FFPROBE_BIN` |
| 混音比画布短 0.1s | 不要用最终 `loudnorm`；`build_mix` 用定长 PCM + 峰值归一 |
| 切换时旧内容压住新背景 | 每个 `.screen` 必须有 `z-index:1`，否则旧内容 z-index 2 会盖住新背景 |
| 底栏窄段序号溢出 | 尾屏段窄：`vseg-outro` 隐藏 `v-idx` 并缩小间距 |
| 检查报 `text_box_overflow` | 加宽容器或缩短文案，不要用 `data-layout-ignore` 掩盖 |
| `check` 报 `text_below_floor` / `line_unread` | 建议项：能缩短卡片文案就改；标签类小字不阻塞 |
| 抽帧在某时刻是空白 | 内容从切换点 `+0.5s` 才入场；换到切换点 `+0.6s` 之后抽帧 |

## 验收口径

- `check`：0 error 才继续。
- `snapshot`：至少看封面、两条故事、一条尾屏；来源截图要能读。
- `verify_render.py`：确认 3840×2160 / 30fps / AAC 48k；点击音 `peak ≥ 0.10`。