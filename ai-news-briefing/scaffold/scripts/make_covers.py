#!/usr/bin/env python3
"""根据 content.json 生成 16:9 与 4:3 的 B 站风格封面。"""

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

LOGO_MAP = {
    "openai": ("openai.svg", "OpenAI"),
    "anthropic": ("anthropic.svg", "Anthropic"),
    "meta": ("meta.svg", "Meta"),
    "kimi": ("kimi.svg", "Kimi"),
    "minimax": ("minimax.svg", "MiniMax"),
    "kuaishou": ("kuaishou.svg", "快手·可灵"),
    "vllm": ("vllm.svg", "vLLM"),
    "deepseek": ("deepseek.svg", "DeepSeek"),
}

VENDOR_KEY = {
    "OpenAI": "openai",
    "Anthropic": "anthropic",
    "Meta": "meta",
    "Kimi": "kimi",
    "MiniMax": "minimax",
    "快手": "kuaishou",
    "Kuaishou": "kuaishou",
    "vLLM": "vllm",
    "DeepSeek": "deepseek",
}


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


def logo_keys(cover: dict, stories: list[dict]) -> list[str]:
    explicit = cover.get("logos")
    if explicit:
        return [key for key in explicit if key in LOGO_MAP][:8]
    keys = []
    for story in stories:
        key = VENDOR_KEY.get(story.get("vendor"))
        if key and key not in keys:
            keys.append(key)
    return keys[:6] or ["openai", "anthropic", "meta", "kimi", "minimax", "kuaishou"]


def logo_cell(key: str, project: Path) -> str:
    filename, name = LOGO_MAP.get(key, (None, key))
    src = project / "assets" / "logos" / filename if filename else None
    if src and src.exists():
        visual = f'<img src="{src.resolve().as_uri()}" alt="{esc(name)}" />'
    else:
        visual = f'<span class="logo-word">{esc(name)}</span>'
    return f'<div class="logo"><div class="logo-img">{visual}</div><span>{esc(name)}</span></div>'


def font_size(lines: list[str], base: int) -> int:
    longest = max((len(line) for line in lines), default=1)
    if longest > 9:
        return int(base * 0.62)
    if longest > 7:
        return int(base * 0.74)
    if longest > 5:
        return int(base * 0.86)
    return base


def build_html(content: dict, variant: str, project: Path) -> str:
    cover = content["screens"][0]
    stories = [s for s in content["screens"] if s.get("type") == "story"]
    meta = content.get("meta", {})
    date = meta.get("date", "")
    issue = meta.get("issue", cover.get("issueStamp", ""))
    headline = cover.get("headline") or cover.get("title", "")
    hook_lines = cover.get("hook_lines") or [headline]
    accent_index = cover.get("hook_accent", len(hook_lines) - 1)
    subhook = cover.get("subhook") or cover.get("subtitle", "")
    meta_line = cover.get("subtitle", "")
    keys = logo_keys(cover, stories)
    logos = "".join(logo_cell(key, project) for key in keys)
    hook_size = font_size(hook_lines, 226 if variant == "16x9" else 172)
    hook_html = []
    for index, line in enumerate(hook_lines):
        cls = "line accent" if index == accent_index else "line"
        hook_html.append(f'<span class="{cls}">{esc(line)}</span>')
    font_sans = (project / "assets" / "fonts" / "NotoSansSC-VF.ttf").resolve().as_uri()
    font_serif = (project / "assets" / "fonts" / "NotoSerifSC-VF.ttf").resolve().as_uri()
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<style>
@font-face {{ font-family: "HF Sans"; src: url("{font_sans}") format("truetype"); font-weight: 100 900; font-display: block; }}
@font-face {{ font-family: "HF Serif"; src: url("{font_serif}") format("truetype"); font-weight: 100 900; font-display: block; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; background: #141210; color: #F7F1E4; font-family: "HF Sans", sans-serif; }}
.cover {{ position: relative; width: 100vw; height: 100vh; overflow: hidden;
  background:
    radial-gradient(circle at 10% 8%, rgba(232,93,42,.24), transparent 34%),
    radial-gradient(circle at 92% 88%, rgba(247,241,228,.06), transparent 40%),
    #141210; }}
.cover::after {{ content: ""; position: absolute; inset: 0; pointer-events: none; opacity: .16;
  background-image: radial-gradient(rgba(247,241,228,.16) .6px, transparent .6px);
  background-size: 5px 5px; }}
.topbar {{ position: absolute; top: 50px; left: 64px; right: 64px; display: flex;
  justify-content: space-between; align-items: center; z-index: 2; }}
.brand {{ display: flex; align-items: center; gap: 12px; font-weight: 800; font-size: 26px; letter-spacing: .08em; }}
.brand i {{ width: 12px; height: 12px; border-radius: 50%; background: #E85D2A; display: inline-block; }}
.date {{ font-size: 17px; letter-spacing: .08em; color: #A99B8C; }}
.layout {{ position: absolute; left: 56px; right: 56px; top: 120px; bottom: 72px; display: grid;
  grid-template-columns: 1.55fr .85fr; gap: 44px; z-index: 2; }}
.copy {{ min-width: 0; display: flex; flex-direction: column; justify-content: center; }}
.hook {{ font-family: "HF Serif", serif; font-weight: 900; font-size: {hook_size}px;
  line-height: .92; letter-spacing: -.05em; max-width: 1180px; }}
.hook .line {{ display: block; white-space: nowrap; }}
.hook .accent {{ display: inline-block; margin-top: 18px; padding: 0 14px 4px;
  background: #E85D2A; color: #141210; }}
.subhook {{ margin: 32px 0 0; font-size: 44px; line-height: 1.3; letter-spacing: -.015em; color: #F7F1E4; max-width: 1150px; }}
.meta {{ margin: 16px 0 0; font-size: 22px; letter-spacing: .05em; color: #B8A999; }}
.logos {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 26px 14px;
  align-content: center; justify-items: center; }}
.logo {{ text-align: center; min-width: 0; }}
.logo-img {{ width: 112px; height: 112px; display: grid; place-items: center; margin: 0 auto 10px; }}
.logo-img img {{ width: 100px; height: 100px; object-fit: contain; filter: brightness(0) invert(1); }}
.logo-img .logo-word {{ font-size: 26px; font-weight: 800; color: #F7F1E4; white-space: nowrap; }}
.logo span {{ display: block; font-size: 18px; color: #D3C5B4; letter-spacing: .02em; white-space: nowrap; }}
.issue {{ position: absolute; right: 30px; bottom: 40px; z-index: 1;
  font-family: Georgia, serif; font-size: 210px; line-height: .8; letter-spacing: -.06em;
  color: rgba(247,241,228,.05); }}
.foot {{ position: absolute; left: 64px; right: 64px; bottom: 26px; display: flex;
  justify-content: space-between; font-size: 15px; letter-spacing: .08em; color: #A99B8C; z-index: 2; }}
.portrait .layout {{ display: grid; grid-template-columns: 1.3fr .7fr; gap: 24px; top: 100px; bottom: 64px; left: 48px; right: 48px; }}
.portrait .copy {{ justify-content: center; }}
.portrait .hook {{ font-size: {hook_size}px; max-width: 880px; }}
.portrait .subhook {{ font-size: 32px; margin-top: 24px; max-width: 840px; }}
.portrait .meta {{ font-size: 19px; margin-top: 12px; }}
.portrait .logos {{ grid-template-columns: repeat(2, 1fr); gap: 22px 10px; align-content: center;
  justify-items: center; border-top: 0; padding-top: 0; margin-top: 0; }}
.portrait .logo-img {{ width: 96px; height: 96px; margin-bottom: 7px; }}
.portrait .logo-img img {{ width: 88px; height: 88px; }}
.portrait .logo span {{ font-size: 16px; }}
.portrait .issue {{ font-size: 150px; right: 24px; bottom: 40px; }}
</style>
</head>
<body>
<div class="cover {'portrait' if variant == '4x3' else 'landscape'}">
  <header class="topbar">
    <div class="brand"><i></i>AI 早报</div>
    <div class="date">{esc(date)} · {esc(issue)}</div>
  </header>
  <main class="layout">
    <section class="copy">
      <div class="hook">{''.join(hook_html)}</div>
      <p class="subhook">{esc(subhook)}</p>
      <p class="meta">{esc(meta_line)}</p>
    </section>
    <aside class="logos">{logos}</aside>
  </main>
  <div class="issue">{esc(issue)}</div>
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
                "headline": content["screens"][0].get("headline") or content["screens"][0].get("title", ""),
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
    parser = argparse.ArgumentParser(description="生成 16:9 与 4:3 B 站风格封面")
    parser.add_argument("--project", default=".", help="工程目录")
    args = parser.parse_args()
    for path in generate_covers(Path(args.project)):
        print(path)