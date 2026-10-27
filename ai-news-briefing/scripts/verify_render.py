#!/usr/bin/env python3
"""验收 AI 早报成片：容器规格、时长、音轨和切换点点击音。"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path


def resolve_bin(name: str, env_key: str) -> str | None:
    env = os.environ.get(env_key)
    if env and Path(env).exists():
        return env
    found = shutil.which(name)
    return found


def probe(ffprobe: str, video: Path) -> dict:
    out = subprocess.run(
        [
            ffprobe, "-v", "error",
            "-show_entries", "format=duration,size,bit_rate",
            "-show_entries", "stream=index,codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels",
            "-of", "json", str(video),
        ],
        capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout)


def click_report(mix: Path, timeline: Path) -> list[str]:
    try:
        import numpy as np
        import soundfile as sf
    except ImportError:
        return ["soundfile/numpy 未安装，跳过点击音检查"]
    data = json.loads(timeline.read_text(encoding="utf-8"))
    audio, sr = sf.read(str(mix))
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    lines = []
    for tr in data.get("transitions", []):
        at = float(tr.get("clickAt", tr["at"]))
        pre = audio[int((at - 0.12) * sr):int((at - 0.02) * sr)]
        hit = audio[int(at * sr):int((at + 0.10) * sr)]
        if hit.size == 0:
            continue
        pre_peak = float(np.max(np.abs(pre))) if pre.size else 0.0
        hit_peak = float(np.max(np.abs(hit)))
        lines.append(f"  {at:6.2f}s peak={hit_peak:.3f} quiet={pre_peak:.3f}")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="验收 AI 早报成片")
    parser.add_argument("video", help="成片 MP4 路径")
    parser.add_argument("--mix", default="assets/audio/mix.wav", help="混音文件，用于点击音检查")
    parser.add_argument("--timeline", default="assets/audio/timeline.json", help="时间轴文件")
    args = parser.parse_args()

    video = Path(args.video).resolve()
    if not video.exists():
        print(f"[fail] 找不到 {video}")
        return 1
    ffprobe = resolve_bin("ffprobe", "FFPROBE_BIN")
    if not ffprobe:
        print("[fail] 找不到 ffprobe，设置 FFPROBE_BIN 或加入 PATH")
        return 1

    info = probe(ffprobe, video)
    video_stream = next((s for s in info["streams"] if s["codec_type"] == "video"), {})
    audio_stream = next((s for s in info["streams"] if s["codec_type"] == "audio"), {})
    print(f"[video] {video}")
    print(
        f"[spec] {video_stream.get('width')}x{video_stream.get('height')} "
        f"{video_stream.get('r_frame_rate')} {info['format'].get('duration')}s "
        f"{int(info['format'].get('size', 0)) / 1024 / 1024:.1f}MB"
    )
    print(
        f"[audio] {audio_stream.get('codec_name')} {audio_stream.get('sample_rate')}Hz "
        f"{audio_stream.get('channels')}ch"
    )

    mix = Path(args.mix)
    timeline = Path(args.timeline)
    if mix.exists() and timeline.exists():
        print("[clicks]")
        for line in click_report(mix, timeline):
            print(line)
    else:
        print("[clicks] 缺少 mix.wav 或 timeline.json，跳过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())