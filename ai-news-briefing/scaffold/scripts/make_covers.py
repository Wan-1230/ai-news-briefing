#!/usr/bin/env python3
"""根据 content.json 生成 16:9 与 4:3 横屏封面。"""

from __future__ import annotations

import html
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

VARIANTS = (
    ("16x9", 1920, 1080, 1920, 1080),
    ("4x3", 1440, 1080, 1440, 1080),
)


def find_chromium() -> Path | None:
    env = os.environ.get("AI_BRIEFING_CHROMIUM")
    if env and Path(env).exists():
        return Path(env)
    for root in (
        Path.home() / "AppData" / "Local" / "ms-playwright",
        Path.home() / ".cache" / "ms-playwright",
        Path("/ms-playwright"),
    ):
        if not root.exists():
            continue
        for pattern in (
            "chromium-*/chrome-win64/chrome.exe",
            "chromium-*/chrome-linux/chrome",
            "chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium",
        ):
            matches = sorted(root.glob(pattern), reverse=True)
            if matches:
                return matches[0]
    return None


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def category_color(content: dict, category: str) -> str:
    for screen in content["screens"]:
        if screen.get("category") == category:
            return screen.get("categoryColor") or "#C8552C"
    return "#C8552C"


def vendor_color(content: dict, vendor: str) -> str:
    for screen in content["screens"]:
        if screen.get("vendor") == vendor:
            return screen.get("vendorColor") or "#2B2620"
    return "#2B2620"


def build_html(content: dict, variant: str, project: Path) -> str:
    cover = content["screens"][0]
    stories = [s for s in content["screens"] if s["type"] == "story"]
    meta = content.get("meta", {})
    date = meta.get("date", cover.get("kicker", ""))
    issue = meta.get("issue", cover.get("issueStamp", ""))
    title = cover.get("title", "")
    subtitle = cover.get("subtitle", "")
    kicker = cover.get("kicker", f"AI 早报 · {date}")
    caption = cover.get("caption", "欢迎收听今天的 AI 早报")
    all_index = cover.get("index", [])
    index = all_index[:4] if variant == "16x9" else all_index[:8]
    rows = []
    for i, item in enumerate(index, 1):
        color = category_color(content, item.get("cat", "要闻"))
        rows.append(
            '<div class="row">'
            f'<span class="no">{i:02d}</span>'
            f'<span class="cat" style="--c:{esc(color)}"><i></i>{esc(item.get("cat", "要闻"))}</span>'
            f'<span class="text">{esc(item.get("text", ""))}</span>'
            "</div>"
        )
    vendors = []
    seen = set()
    for story in stories:
        vendor = story.get("vendor")
        if not vendor or vendor in seen:
            continue
        seen.add(vendor)
        vendors.append(
            f'<span class="chip"><i style="background:{esc(vendor_color(content, vendor))}"></i>{esc(vendor)}</span>'
        )
        if len(vendors) >= 7:
            break
    font_sans = (project / "assets" / "fonts" / "NotoSansSC-VF.ttf").resolve().as_uri()
    font_serif = (project / "assets" / "fonts" / "NotoSerifSC-VF.ttf").resolve().as_uri()
    more = len(stories) - len(index)
    more_line = f'<div class="more">还有 {more} 条，详见视频</div>' if more > 0 else ""
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<style>
@font-face {{ font-family: "HF Sans"; src: url("{font_sans}") format("truetype"); font-weight: 100 900; font-display: block; }}
@font-face {{ font-family: "HF Serif"; src: url("{font_serif}") format("truetype"); font-weight: 100 900; font-display: block; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; background: #F7F1E4; color: #2B2620; font-family: "HF Sans", sans-serif; }}
.cover {{ position: relative; width: 100vw; height: 100vh; overflow: hidden;
  background:
    radial-gradient(circle at 88% 6%, rgba(200,85,44,.12), transparent 34%),
    radial-gradient(circle at 8% 96%, rgba(90,90,140,.08), transparent 38%),
    #F7F1E4; }}
.cover::after {{ content: ""; position: absolute; inset: 0; pointer-events: none; opacity: .22;
  background-image: radial-gradient(rgba(43,38,32,.10) .6px, transparent .6px);
  background-size: 5px 5px; }}
.masthead {{ position: absolute; top: 52px; left: 64px; right: 64px; display: flex;
  justify-content: space-between; align-items: center; z-index: 2; }}
.brand {{ display: flex; align-items: center; gap: 12px; font-weight: 800; font-size: 26px; letter-spacing: .08em; }}
.brand i {{ width: 12px; height: 12px; border-radius: 50%; background: #C8552C; display: inline-block; }}
.date-line {{ font-size: 18px; letter-spacing: .10em; color: #6E6459; }}
.layout {{ position: absolute; left: 64px; right: 64px; top: 138px; bottom: 74px; display: grid;
  grid-template-columns: 1.62fr .78fr; gap: 54px; z-index: 2; }}
.copy {{ min-width: 0; }}
.kicker {{ font-size: 18px; letter-spacing: .12em; color: #A8461F; margin-bottom: 22px; }}
.title {{ margin: 0; font-family: "HF Serif", serif; font-weight: 900; font-size: 104px;
  line-height: 1.08; letter-spacing: -.03em; max-width: 1100px; }}
.sub {{ margin: 24px 0 0; font-size: 27px; line-height: 1.5; color: #5F564B; }}
.rule {{ width: 120px; height: 5px; border-radius: 3px; background: #C8552C; margin: 30px 0 24px; }}
.headlines {{ display: flex; flex-direction: column; gap: 0; }}
.row {{ display: grid; grid-template-columns: 42px 104px 1fr; gap: 14px; align-items: center;
  padding: 13px 0; border-bottom: 1px solid rgba(228,218,203,.85); }}
.row:last-child {{ border-bottom: 0; }}
.no {{ font-family: Georgia, serif; font-size: 20px; color: #6B6156; }}
.cat {{ display: inline-flex; align-items: center; gap: 7px; padding: 5px 9px; border: 1px solid #E4DACB;
  border-radius: 999px; font-size: 14px; color: #6E6459; white-space: nowrap; }}
.cat i {{ width: 7px; height: 7px; border-radius: 50%; background: var(--c); }}
.text {{ font-size: 24px; line-height: 1.35; color: #2B2620; }}
.side {{ position: relative; display: flex; flex-direction: column; align-items: flex-start;
  justify-content: flex-end; padding-bottom: 10px; }}
.issue {{ font-family: Georgia, serif; font-size: 210px; line-height: .85; letter-spacing: -.06em;
  color: rgba(43,38,32,.10); position: absolute; top: -8px; right: 0; }}
.counts {{ display: flex; align-items: baseline; gap: 10px; font-size: 18px; color: #6E6459; }}
.counts strong {{ font-family: Georgia, serif; font-size: 48px; color: #C8552C; font-weight: 700; }}
.chips {{ display: flex; flex-wrap: wrap; gap: 9px; margin-top: 22px; }}
.chip {{ display: inline-flex; align-items: center; gap: 7px; padding: 7px 11px; border: 1px solid #E4DACB;
  border-radius: 999px; background: rgba(255,253,248,.7); font-size: 16px; color: #5F564B; }}
.chip i {{ width: 8px; height: 8px; border-radius: 50%; }}
.more {{ margin-top: 14px; font-size: 15px; color: #6E6459; letter-spacing: .04em; }}
.source-note {{ margin-top: 24px; font-size: 15px; line-height: 1.7; color: #6E6459; }}
.quote {{ margin-top: 26px; padding-left: 18px; border-left: 4px solid #C8552C;
  font-family: "HF Serif", serif; font-size: 34px; line-height: 1.4; color: #5F564B; }}
.side-quote {{ margin: 0 0 28px; padding-left: 0; border-left: 0; font-size: 26px; color: #6E6459; }}
.foot {{ position: absolute; left: 64px; right: 64px; bottom: 28px; display: flex;
  justify-content: space-between; font-size: 15px; letter-spacing: .08em; color: #6E6459; z-index: 2; }}
.portrait .layout {{ display: flex; flex-direction: column; gap: 14px; top: 116px; bottom: 60px; }}
.portrait .title {{ font-size: 76px; max-width: 1280px; line-height: 1.1; }}
.portrait .sub {{ font-size: 24px; margin-top: 14px; }}
.portrait .rule {{ margin: 18px 0 12px; }}
.portrait .row {{ padding: 8px 0; grid-template-columns: 34px 92px 1fr; }}
.portrait .text {{ font-size: 20px; }}
.portrait .side {{ display: flex; flex-direction: row; align-items: center; gap: 24px; margin-top: auto;
  width: 100%; padding: 16px 0 4px; border-top: 1px solid rgba(228,218,203,.85); }}
.portrait .side-quote, .portrait .issue {{ display: none; }}
.portrait .quote {{ margin-top: 24px; font-size: 34px; max-width: 1100px; }}
.portrait .issue {{ font-size: 150px; top: -34px; right: 0; opacity: .07; }}
.portrait .counts strong {{ font-size: 36px; }}
.portrait .chips {{ margin-top: 0; }}
.portrait .source-note, .portrait .more {{ display: none; }}
</style>
</head>
<body>
<div class="cover {'portrait' if variant == '4x3' else 'landscape'}">
  <header class="masthead">
    <div class="brand"><i></i>AI 早报</div>
    <div class="date-line">{esc(date)} · {esc(issue)}</div>
  </header>
  <main class="layout">
    <section class="copy">
      <div class="kicker">{esc(kicker)}</div>
      <h1 class="title">{esc(title)}</h1>
      <p class="sub">{esc(subtitle)}</p>
      <div class="rule"></div>
      <div class="headlines">{''.join(rows)}</div>
      <div class="quote">“{esc(caption)}”</div>
    </section>
    <aside class="side">
      <div class="issue">{esc(issue)}</div>
      <div class="quote side-quote">“{esc(caption)}”</div>
      <div class="counts"><strong>{len(stories)}</strong><span>条要闻</span><strong>{len(stories)}</strong><span>个来源</span></div>
      <div class="chips">{''.join(vendors)}</div>
      {more_line}
      <div class="source-note">每条附原文截图<br>可信参考</div>
    </aside>
  </main>
  <footer class="foot"><span>AI 早报 · {esc(issue)}</span><span>{esc(date)} · 公开信息整理</span></footer>
</div>
</body>
</html>'''


def generate_covers(project: Path, chromium: str | None = None) -> list[Path]:
    project = project.resolve()
    content = json.loads((project / "content.json").read_text(encoding="utf-8"))
    out_dir = project / "out" / "covers"
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    exe = Path(chromium) if chromium else find_chromium()
    with sync_playwright() as p:
        launch = {"headless": True}
        if exe and exe.exists():
            launch["executable_path"] = str(exe)
        browser = p.chromium.launch(**launch)
        for name, width, height, out_w, out_h in VARIANTS:
            html_path = out_dir / f"cover_{name}.html"
            html_path.write_text(build_html(content, name, project), encoding="utf-8")
            page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=2, locale="zh-CN")
            page.goto(html_path.as_uri())
            page.evaluate("() => document.fonts.ready.then(() => true)")
            page.wait_for_timeout(350)
            png = out_dir / f"cover_{name}.png"
            page.screenshot(path=str(png))
            page.close()
            image = Image.open(png).convert("RGB")
            if image.size != (out_w, out_h):
                image = image.resize((out_w, out_h), Image.LANCZOS)
                image.save(png, optimize=True)
            jpg = out_dir / f"cover_{name}.jpg"
            image.save(jpg, quality=92, optimize=True)
            outputs.extend([png, jpg])
        browser.close()
    (out_dir / "manifest.json").write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "title": content["screens"][0].get("title", ""),
                "covers": [str(p.relative_to(project)).replace("\\", "/") for p in outputs],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return outputs


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="生成 16:9 与 4:3 横屏封面")
    parser.add_argument("--project", default=".", help="工程目录")
    args = parser.parse_args()
    for path in generate_covers(Path(args.project)):
        print(path)