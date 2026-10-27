#!/usr/bin/env python3
"""从 skill 脚手架创建一个 AI 早报视频工程。"""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SCAFFOLD = SKILL / "scaffold"
FONTS = ("NotoSansSC-VF.ttf", "NotoSerifSC-VF.ttf")
DIRS = ("assets/audio/raw", "assets/evidence", "assets/fonts", "out")


def find_fonts(explicit: str | None, target: Path) -> Path | None:
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    env = os.environ.get("AI_BRIEFING_FONTS")
    if env:
        candidates.append(Path(env))
    candidates += [
        target / "assets" / "fonts",
        SKILL / "assets" / "fonts",
        Path.cwd() / "hf_news" / "assets" / "fonts",
        Path.home() / "Documents" / "hf_news" / "assets" / "fonts",
    ]
    for candidate in candidates:
        if candidate.is_dir() and all((candidate / f).exists() for f in FONTS):
            return candidate
    return None


def copy_scaffold(target: Path) -> list[str]:
    copied = []
    for src in sorted(SCAFFOLD.rglob("*")):
        if not src.is_file() or "__pycache__" in src.parts:
            continue
        rel = src.relative_to(SCAFFOLD)
        dst = target / rel
        if dst.exists():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied.append(str(rel).replace("\\", "/"))
    return copied


def main() -> int:
    parser = argparse.ArgumentParser(description="创建 AI 早报视频工程")
    parser.add_argument("--dir", required=True, help="工程目录")
    parser.add_argument("--fonts-dir", default=None, help="Noto Sans SC / Noto Serif SC 可变字体所在目录")
    parser.add_argument("--tts-model", default=None, help="Qwen3-TTS 模型目录，写入 env 提示")
    args = parser.parse_args()

    target = Path(args.dir).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    copied = copy_scaffold(target)
    for rel in DIRS:
        (target / rel).mkdir(parents=True, exist_ok=True)

    fonts_from = find_fonts(args.fonts_dir, target)
    missing_fonts = []
    if fonts_from and fonts_from != target / "assets" / "fonts":
        for name in FONTS:
            src = fonts_from / name
            dst = target / "assets" / "fonts" / name
            if src.exists() and not dst.exists():
                shutil.copy2(src, dst)
    missing_fonts = [f for f in FONTS if not (target / "assets" / "fonts" / f).exists()]

    tts_model = args.tts_model or os.environ.get("AI_BRIEFING_TTS_MODEL") or "<Qwen3-TTS 模型目录>"
    print(f"[project] {target}")
    print(f"[copied] {len(copied)} files")
    for rel in copied:
        print(f"  - {rel}")
    if missing_fonts:
        print("[fonts] 缺失：" + ", ".join(missing_fonts))
        print("[fonts] 用 --fonts-dir 指向已有字体目录，或将字体放入 <project>/assets/fonts/")
    else:
        print("[fonts] ok")
    print("[next] 设置环境变量（按需）：")
    print(f'  export AI_BRIEFING_TTS_MODEL="{tts_model}"')
    print('  export AI_BRIEFING_CHROMIUM="<chromium chrome.exe>"')
    print('  export FFMPEG_BIN="<ffmpeg.exe>"')
    print('  export FFPROBE_BIN="<ffprobe.exe>"')
    print("[next] 在工程目录运行：")
    print("  python scripts/collect_daily.py --top 20 --recommend 8")
    print("  python scripts/capture_evidence.py --plan assets/evidence/evidence_plan.json")
    print("  写 content.json，然后 python build.py --speed 1.68")
    return 0 if not missing_fonts else 1


if __name__ == "__main__":
    raise SystemExit(main())