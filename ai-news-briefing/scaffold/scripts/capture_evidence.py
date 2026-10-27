#!/usr/bin/env python3
"""抓取新闻原文截图，作为视频里的可信参考依据。"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

HF_NEWS = Path(__file__).resolve().parents[1]
OUT = HF_NEWS / "assets" / "evidence"
TEXT = HF_NEWS / "out" / "evidence_text"

ITEMS = [
    {
        "id": "anthropic_ipo",
        "url": "https://www.anthropic.com/news/s1-sec",
        "label": "官方公告",
        "source": "anthropic.com",
    },
    {
        "id": "meta_funding",
        "url": "https://www.ithome.com/1/018/144.htm",
        "label": "媒体报道",
        "source": "ithome.com",
    },
    {
        "id": "kling_4",
        "url": "https://www.jiemian.com/article/15220180.html",
        "label": "媒体报道",
        "source": "jiemian.com",
    },
    {
        "id": "openai_decisions",
        "url": "https://m.itbear.com.cn/html/2026-10/1577331.html",
        "label": "媒体报道",
        "source": "itbear.com.cn",
    },
    {
        "id": "kimi_k31",
        "url": "https://www.kimi.com/en/blog/kimi-k3-1-pro",
        "label": "官方博客",
        "source": "kimi.com",
    },
    {
        "id": "minimax_m31",
        "url": "http://36kr.com/p/4038403667760257",
        "label": "媒体报道",
        "source": "36kr.com",
    },
    {
        "id": "anthropic_alignment",
        "url": "https://www.anthropic.com/research/alignment-assessment-ukaisi",
        "label": "官方研究",
        "source": "anthropic.com",
    },
    {
        "id": "vllm_toolcall",
        "url": "https://www.ubicloud.com/blog/fixing-tool-call-accuracy-in-vllm",
        "label": "技术博客",
        "source": "ubicloud.com",
    },
]

HIDE_CSS = """
[class*="cookie"], [class*="consent"], [id*="cookie"], [id*="consent"],
[class*="login-modal"], [class*="loginModal"], [id*="login-modal"],
[class*="login-bar"], [class*="loginBar"], .modal-mask, .mask-layer,
.fixed-mask, .overlay-mask, .app-download, .download-bar {
  display: none !important;
}
"""

def find_chromium() -> Path | None:
    env = os.environ.get("AI_BRIEFING_CHROMIUM")
    if env and Path(env).exists():
        return Path(env)
    roots = [
        Path.home() / "AppData" / "Local" / "ms-playwright",
        Path.home() / ".cache" / "ms-playwright",
        Path("/ms-playwright"),
    ]
    patterns = (
        "chromium-*/chrome-win64/chrome.exe",
        "chromium-*/chrome-linux/chrome",
        "chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium",
    )
    for root in roots:
        if not root.exists():
            continue
        for pattern in patterns:
            matches = sorted(root.glob(pattern), reverse=True)
            if matches:
                return matches[0]
    return None


def load_plan(path: Path) -> list[dict]:
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data.get("items", data) if isinstance(data, dict) else data
        if isinstance(items, list) and items:
            return items
    return ITEMS


def main() -> int:
    parser = argparse.ArgumentParser(description="抓取新闻原文截图，作为视频里的可信参考依据")
    parser.add_argument("--plan", default=str(HF_NEWS / "assets" / "evidence" / "evidence_plan.json"))
    parser.add_argument("--out-dir", default=str(OUT))
    parser.add_argument("--text-dir", default=str(TEXT))
    parser.add_argument("--chromium", default=os.environ.get("AI_BRIEFING_CHROMIUM", ""))
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    text_dir = Path(args.text_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    text_dir.mkdir(parents=True, exist_ok=True)
    items = load_plan(Path(args.plan))
    exe = Path(args.chromium) if args.chromium else find_chromium()
    manifest = []
    with sync_playwright() as p:
        launch = {"headless": True}
        if exe and exe.exists():
            launch["executable_path"] = str(exe)
        browser = p.chromium.launch(**launch)
        for item in items:
            page = browser.new_page(
                viewport={"width": 1440, "height": 900},
                device_scale_factor=1.5,
                locale="zh-CN",
            )
            image_path = out_dir / f"{item['id']}.png"
            try:
                image_rel = image_path.relative_to(HF_NEWS).as_posix()
            except ValueError:
                image_rel = str(image_path)
            record = {
                "id": item["id"],
                "url": item["url"],
                "label": item.get("label", "可信参考"),
                "source": item.get("source", ""),
                "position": item.get("position", "top center"),
                "fit": item.get("fit", "cover"),
                "captured_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "image": image_rel,
            }
            try:
                page.goto(item["url"], wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(2200)
                page.add_style_tag(content=HIDE_CSS)
                h1 = ""
                if page.locator("h1").count():
                    locator = page.locator("h1").first
                    h1 = locator.inner_text().strip()
                    locator.scroll_into_view_if_needed()
                    page.wait_for_timeout(700)
                    page.evaluate("window.scrollBy(0, -90)")
                    page.wait_for_timeout(500)
                body = page.locator("body").inner_text()[:6000]
                (text_dir / f"{item['id']}.txt").write_text(body, encoding="utf-8")
                page.screenshot(path=str(image_path), full_page=False)
                record.update({
                    "status": "ok",
                    "final_url": page.url,
                    "title": page.title(),
                    "h1": h1,
                    "text_excerpt": body[:500],
                })
                print(f"[ok] {item['id']} {page.url}", flush=True)
            except Exception as exc:
                record.update({"status": "error", "error": f"{type(exc).__name__}: {exc}"})
                print(f"[err] {item['id']} {type(exc).__name__}: {str(exc)[:140]}", flush=True)
            finally:
                page.close()
            manifest.append(record)
        browser.close()
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[manifest] {out_dir / 'manifest.json'}")
    return 0 if all(x["status"] == "ok" for x in manifest) else 1


if __name__ == "__main__":
    sys.exit(main())
