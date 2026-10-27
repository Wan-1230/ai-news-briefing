#!/usr/bin/env python3
"""Build the HyperFrames AI-news demo end to end.

Pipeline: narration -> trimmed/mastered voice -> timeline -> audio mix ->
generated index.html (HyperFrames composition). The HTML/GSAP layer is fully
local; no render-time network requests.
"""
from __future__ import annotations

import argparse
import html
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

PROJ = Path(__file__).resolve().parent
ROOT = PROJ.parent


def resolve_bin(name: str, env_key: str) -> Path:
    env = os.environ.get(env_key)
    if env and Path(env).exists():
        return Path(env)
    for base in (ROOT, PROJ.parent, PROJ):
        candidate = base / "tools" / "bin" / f"{name}.exe"
        if candidate.exists():
            return candidate
    found = shutil.which(name)
    return Path(found) if found else ROOT / "tools" / "bin" / f"{name}.exe"


def resolve_model() -> Path:
    env = os.environ.get("AI_BRIEFING_TTS_MODEL")
    candidates = [Path(env)] if env else []
    candidates += [
        ROOT / "models" / "qwen-tts-0.6b",
        PROJ.parent / "models" / "qwen-tts-0.6b",
        PROJ / "models" / "qwen-tts-0.6b",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return ROOT / "models" / "qwen-tts-0.6b"


FF = resolve_bin("ffmpeg", "FFMPEG_BIN")
FP = resolve_bin("ffprobe", "FFPROBE_BIN")
MODEL = resolve_model()
AUDIO = PROJ / "assets" / "audio"
RAW = AUDIO / "raw"

SR = 48000
LEAD_IN = 0.85
VOICE_GAP = 0.24
TRANSITION_WINDOW = 0.56
TAIL_HOLD = 2.00

INK = "#2B2620"
MUTED = "#6E6459"
ORANGE = "#C8552C"
ORANGE_DEEP = "#A8461F"
CREAM = "#F7F1E4"
DOCK = "#ECEDE1"
TRACK = "#D9D4C4"

CAT_FALLBACK = {
    "要闻": "#C8552C",
    "开发生态": "#3E6B5A",
    "模型发布": "#5A5A8C",
    "产品应用": "#B07A2A",
    "技术与洞察": "#4C6A7A",
    "行业动态": "#8A6A3A",
    "前沿与传闻": "#7A5A6E",
}

ICONS = {
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/><path d="M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01"/>',
    "refresh": '<path d="M20 11a8 8 0 1 0-2.3 5.7"/><path d="M20 4v7h-7"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "workflow": '<rect x="3" y="3" width="6" height="6" rx="1.5"/><rect x="15" y="15" width="6" height="6" rx="1.5"/><path d="M9 6h4a2 2 0 0 1 2 2v7"/><path d="M15 15h-4a2 2 0 0 1-2-2V6"/>',
    "cube": '<path d="M12 3 3 8l9 5 9-5-9-5Z"/><path d="M3 8v8l9 5 9-5V8"/><path d="M12 13v8"/>',
    "layout": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M9 9v11"/>',
    "monitor": '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>',
    "spark": '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Z"/><path d="M19 17l.8 2.2L22 20l-2.2.8L19 23l-.8-2.2L16 20l2.2-.8L19 17Z"/>',
    "moon": '<path d="M20 15.5A8.5 8.5 0 0 1 8.5 4 8.5 8.5 0 1 0 20 15.5Z"/>',
    "users": '<circle cx="9" cy="8" r="3"/><path d="M3 20a6 6 0 0 1 12 0"/><path d="M16 5a3 3 0 0 1 0 6M18 20a6 6 0 0 0-3-5.2"/>',
}


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def run(cmd):
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise RuntimeError("command failed:\n" + " ".join(map(str, cmd)) + "\n" + proc.stderr[-4000:])
    return proc.stdout


def duration_of(path: Path) -> float:
    out = run([
        str(FP), "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ]).strip()
    return float(out)


def master_voice(raw: Path, out: Path, speed: float) -> None:
    af = (
        "silenceremove=start_periods=1:start_duration=0.03:start_threshold=-48dB:detection=peak,"
        "areverse,"
        "silenceremove=start_periods=1:start_duration=0.03:start_threshold=-48dB:detection=peak,"
        "areverse,"
        f"atempo={speed},"
        "highpass=f=75,"
        "equalizer=f=260:t=q:w=1.1:g=-1.5,"
        "equalizer=f=3400:t=q:w=1.3:g=1.6,"
        "acompressor=threshold=-20dB:ratio=2.2:attack=5:release=70,"
        "loudnorm=I=-18:TP=-2:LRA=7,"
        "aresample=48000"
    )
    run([
        str(FF), "-y", "-v", "error", "-i", str(raw), "-af", af,
        "-ac", "1", "-c:a", "pcm_s16le", str(out),
    ])


def make_click(path: Path) -> None:
    sr = SR
    n = int(0.15 * sr)
    t = np.arange(n) / sr
    rng = np.random.default_rng(17)
    noise = rng.standard_normal(n)
    hp = np.diff(noise, prepend=0.0)
    click = hp * np.exp(-t / 0.0035) * 0.55
    click += np.sin(2 * np.pi * 2350 * t) * np.exp(-t / 0.006) * 0.50
    click += np.sin(2 * np.pi * 125 * t) * np.exp(-t / 0.022) * 0.22
    second = 0.045
    m = t >= second
    tt = t[m] - second
    click[m] += (hp[m] * np.exp(-tt / 0.003) * 0.22)
    click[m] += np.sin(2 * np.pi * 1750 * tt) * np.exp(-tt / 0.005) * 0.18
    click *= np.clip((0.15 - t) / 0.03, 0, 1)
    click /= max(1e-9, np.max(np.abs(click))) / 0.92
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), click.astype(np.float32), sr, subtype="PCM_16")


def build_mix(vo_paths, screens, transitions, total: float, click_path: Path, out: Path) -> None:
    n = int(math.ceil(total * SR)) + SR
    mix = np.zeros(n, dtype=np.float64)
    for screen, vo in zip(screens, vo_paths):
        audio, sr = sf.read(str(vo), dtype="float64")
        if sr != SR:
            raise ValueError(f"{vo} is {sr} Hz, expected {SR}")
        at = int(round(screen["voiceStart"] * SR))
        end = at + len(audio)
        if end > len(mix):
            mix = np.pad(mix, (0, end - len(mix)))
        mix[at:end] += audio

    click, sr = sf.read(str(click_path), dtype="float64")
    if sr != SR:
        raise ValueError("click.wav must be 48 kHz")
    for tr in transitions:
        at = int(round(tr["clickAt"] * SR))
        end = at + len(click)
        if end > len(mix):
            mix = np.pad(mix, (0, end - len(mix)))
        mix[at:end] += click * 0.48

    rng = np.random.default_rng(23)
    room = rng.standard_normal(len(mix)) * (10 ** (-62 / 20))
    room *= np.linspace(0.0, 1.0, min(len(room), SR // 2)).tolist() + [1.0] * max(0, len(room) - SR // 2)
    mix += room

    n_total = int(round(total * SR))
    if len(mix) < n_total:
        mix = np.pad(mix, (0, n_total - len(mix)))
    mix = mix[:n_total]
    fade = int(0.6 * SR)
    mix[-fade:] *= np.linspace(1.0, 0.0, fade)
    peak = np.max(np.abs(mix))
    if peak > 0:
        # No final loudnorm: it adds ~0.1 s of filter latency and shortens the file.
        # Each VO is already loudness-normalised; keep true peak around -1.3 dBFS.
        mix *= 0.86 / peak
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out), mix.astype(np.float32), SR, subtype="PCM_16")


def build_timeline(content, durations, total: float, nav: list):
    screens = content["screens"]
    rows = []
    for i, (screen, dur) in enumerate(zip(screens, durations)):
        rows.append({
            "id": screen["id"],
            "type": screen["type"],
            "single": bool(screen.get("single", False)),
            "title": screen["title"],
            "category": screen["category"],
            "categoryColor": screen.get("categoryColor") or CAT_FALLBACK.get(screen["category"], ORANGE),
            "vendor": screen["vendor"],
            "vendorColor": screen.get("vendorColor", INK),
            "navIndex": next(j for j, n in enumerate(nav) if n["name"] == screen["nav"]),
            "dur": round(dur, 3),
        })

    voice_start = LEAD_IN
    transitions = []
    for i, row in enumerate(rows):
        row["voiceStart"] = round(voice_start, 3)
        voice_end = voice_start + row["dur"]
        if i < len(rows) - 1:
            at = round(voice_end + VOICE_GAP, 3)
            transitions.append({"from": rows[i]["id"], "to": rows[i + 1]["id"], "at": at})
            voice_start = round(at + TRANSITION_WINDOW, 3)
        else:
            total = round(voice_end + TAIL_HOLD, 3)

    seg_start = 0.0
    for i, row in enumerate(rows):
        row["segStart"] = round(seg_start, 3)
        if i < len(rows) - 1:
            row["segEnd"] = transitions[i]["at"]
            seg_start = transitions[i]["at"]
        else:
            row["segEnd"] = total
        row["leftPct"] = round(row["segStart"] / total * 100, 4)
        row["widthPct"] = round((row["segEnd"] - row["segStart"]) / total * 100, 4)

    groups = []
    for row in rows:
        if groups and groups[-1]["name"] == row["category"]:
            groups[-1]["end"] = row["segEnd"]
            groups[-1]["screenIds"].append(row["id"])
        else:
            groups.append({
                "id": f"g{len(groups)}",
                "name": row["category"],
                "color": row["categoryColor"],
                "start": row["segStart"],
                "end": row["segEnd"],
                "screenIds": [row["id"]],
            })
    for g in groups:
        g["leftPct"] = round(g["start"] / total * 100, 4)
        g["widthPct"] = round((g["end"] - g["start"]) / total * 100, 4)
    group_by_screen = {sid: g["id"] for g in groups for sid in g["screenIds"]}
    group_by_name = {g["name"]: g["id"] for g in groups}

    nav_rows = []
    left = 0.0
    total_w = sum(n["w"] for n in nav)
    for n in nav:
        wp = n["w"] / total_w * 100
        nav_rows.append({"name": n["name"], "leftPct": round(left, 4), "widthPct": round(wp, 4)})
        left += wp

    for row in rows:
        row["navLeftPct"] = nav_rows[row["navIndex"]]["leftPct"]
        row["navWidthPct"] = nav_rows[row["navIndex"]]["widthPct"]
        row["catGroup"] = group_by_screen[row["id"]]
    for i, tr in enumerate(transitions):
        nxt = rows[i + 1]
        tr["clickAt"] = round(tr["at"] + 0.02, 3)
        tr["voiceAt"] = nxt["voiceStart"]
        tr["bandX"] = round(nxt["leftPct"] / 100 * 1784, 2)
        tr["bandScale"] = round(nxt["widthPct"] / 100, 5)
        tr["navIndex"] = nxt["navIndex"]
        tr["navChanged"] = nxt["navIndex"] != rows[i]["navIndex"]
        tr["catGroup"] = nxt["catGroup"]
        tr["catChanged"] = nxt["catGroup"] != rows[i]["catGroup"]

    story_no = 0
    for row in rows:
        if row["type"] == "cover":
            row["order"] = "00"
        elif row["type"] == "outro":
            story_no += 1
            row["order"] = f"{story_no:02d}"
        else:
            story_no += 1
            row["order"] = f"{story_no:02d}"

    return {
        "total": total,
        "fps": 30,
        "timelineWidth": 1784,
        "stageWidth": 1920,
        "stageHeight": 1080,
        "colors": {"ink": INK, "muted": MUTED, "dockMuted": "#4F463C", "orange": ORANGE, "cream": CREAM, "dock": DOCK, "track": TRACK},
        "nav": nav_rows,
        "screens": rows,
        "groups": groups,
        "transitions": transitions,
    }


def icon_svg(name: str) -> str:
    body = ICONS.get(name, ICONS["spark"])
    return (
        '<svg viewBox="0 0 24 24" width="30" height="30" fill="none" '
        'stroke="currentColor" stroke-width="1.7" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true">{body}</svg>'
    )


def render_nav(nav, date: str) -> str:
    items = []
    for i, n in enumerate(nav):
        items.append(
            f'<div class="nav-item" style="width:{n["widthPct"]:.4f}%">'
            f'<span class="nav-label" id="nav-label-{i}">{esc(n["name"])}</span></div>'
        )
    return (
        '<nav class="nav" id="nav">'
        '<div class="nav-items"><div class="nav-pill" id="nav-pill"></div>'
        + "".join(items)
        + '</div>'
        f'<div class="nav-date"><span class="nav-date-dot"></span>{esc(date)}</div>'
        "</nav>"
    )


def render_cover(screen, cats: dict) -> str:
    rows = []
    for i, item in enumerate(screen.get("index", []), 1):
        color = cats.get(item["cat"], ORANGE)
        rows.append(
            '<div class="index-row">'
            f'<span class="index-no">{i:02d}</span>'
            f'<span class="index-cat"><i style="background:{color}"></i>{esc(item["cat"])}</span>'
            f'<span class="index-text">{esc(item["text"])}</span>'
            "</div>"
        )
    stamp = esc(screen.get("issueStamp", "10.24"))
    meta = screen.get("meta") or ["2026-10-24", "公开信息整理", f"{len(screen.get('index', []))} 条要闻"]
    meta_html = "".join(f"<span>{esc(x)}</span>" for x in meta)
    index_count = f"{len(screen.get('index', [])):02d}"
    return f'''
<section class="screen cover" id="screen-{esc(screen["id"])}">
  <div class="screen-bg bg-cover"><span class="wipe-edge"></span></div>
  <div class="screen-inner">
    <div class="issue-stamp" data-layout-ignore="true" data-layout-allow-occlusion="true" aria-hidden="true">{stamp}</div>
    <div class="cover-grid">
      <div class="cover-left">
        <div class="eyebrow"><span class="eyebrow-dot"></span>{esc(screen["kicker"])}</div>
        <h1 class="cover-title">{esc(screen["title"])}</h1>
        <p class="cover-sub">{esc(screen["subtitle"])}</p>
        <div class="cover-rule"></div>
        <div class="cover-meta">{meta_html}</div>
      </div>
      <aside class="cover-index">
        <div class="index-head"><span>今日索引</span><span>{index_count}</span></div>
        {''.join(rows)}
      </aside>
    </div>
    <div class="caption"><div class="caption-pill">{esc(screen["caption"])}</div></div>
  </div>
</section>'''


def render_story(screen) -> str:
    cards = []
    for card in screen.get("cards", []):
        cards.append(
            '<article class="card">'
            f'<div class="card-icon">{icon_svg(card.get("icon", "spark"))}</div>'
            f'<h3>{esc(card["title"])}</h3>'
            f'<p>{esc(card["body"])}</p>'
            "</article>"
        )
    single = " single" if screen.get("single") else ""
    evidence = screen.get("evidence")
    evidence_html = ""
    evidence_class = ""
    if evidence:
        evidence_class = " has-evidence"
        position = evidence.get("position", "top center")
        fit = evidence.get("fit", "cover")
        alt = evidence.get("alt") or f"{screen['title']} 来源页面截图"
        evidence_html = f'''
    <figure class="evidence">
      <div class="evidence-head"><span>来源截图</span><b>{esc(evidence.get("label", "可信参考"))}</b></div>
      <div class="evidence-shot"><img src="{esc(evidence["image"])}" alt="{esc(alt)}" loading="eager" style="object-position:{esc(position)};object-fit:{esc(fit)}" /></div>
      <figcaption class="evidence-foot"><span>{esc(evidence.get("source", ""))}</span><span class="evidence-stamp">{esc(evidence.get("captured", ""))}</span></figcaption>
    </figure>'''
    return f'''
<section class="screen story{single}{evidence_class}" id="screen-{esc(screen["id"])}">
  <div class="screen-bg bg-{esc(screen["id"])}"><span class="wipe-edge"></span></div>
  <div class="screen-inner">
    <div class="story-top">
      <div class="eyebrow"><span class="eyebrow-dot"></span>{esc(screen["kicker"])}</div>
      <div class="issue-no" data-layout-ignore="true" aria-hidden="true">{esc(screen["order"])}</div>
    </div>
    <h1 class="story-title">{esc(screen["title"])}</h1>
    <p class="story-sub">{esc(screen["subtitle"])}</p>
    <div class="story-rule"></div>
    <div class="cards">{''.join(cards)}</div>
    {evidence_html}
    <div class="source"><span class="source-dot"></span>{esc(screen.get("source", "来源 · 公开信息整理"))}</div>
    <div class="vendor-mark" data-layout-ignore="true" aria-hidden="true">{esc(screen["vendor"])}</div>
    <div class="caption"><div class="caption-pill">{esc(screen["caption"])}</div></div>
  </div>
</section>'''


def render_outro(screen) -> str:
    recap = []
    for item in screen.get("recap", []):
        recap.append(
            '<span class="recap-item">'
            f'<i class="recap-dot" style="background:{item["color"]}"></i>{esc(item["name"])}'
            "</span>"
        )
    stamp = esc(screen.get("issueStamp", "10.24"))
    return f'''
<section class="screen outro" id="screen-{esc(screen["id"])}">
  <div class="screen-bg bg-outro"><span class="wipe-edge"></span></div>
  <div class="screen-inner">
    <div class="issue-stamp" data-layout-ignore="true" data-layout-allow-occlusion="true" aria-hidden="true">{stamp}</div>
    <div class="outro-center">
      <div class="eyebrow"><span class="eyebrow-dot"></span>{esc(screen["kicker"])}</div>
      <h1 class="outro-title">{esc(screen["title"])}</h1>
      <p class="outro-sub">{esc(screen["subtitle"])}</p>
      <div class="recap-row">{''.join(recap)}</div>
    </div>
    <div class="caption"><div class="caption-pill">{esc(screen["caption"])}</div></div>
  </div>
</section>'''


def render_screens(screens, cats: dict) -> str:
    parts = []
    for s in screens:
        if s["type"] == "cover":
            parts.append(render_cover(s, cats))
        elif s["type"] == "story":
            parts.append(render_story(s))
        else:
            parts.append(render_outro(s))
    return "\n".join(parts)


def render_dock(timeline, total_tc: str) -> str:
    groups = []
    for g in timeline["groups"]:
        groups.append(
            f'<div class="cat-group" id="cat-{g["id"]}" style="left:{g["leftPct"]:.4f}%;'
            f'width:{g["widthPct"]:.4f}%;--cat:{g["color"]}">'
            f'<span class="cat-line" id="cat-line-{g["id"]}"></span>'
            f'<span class="cat-name" id="cat-name-{g["id"]}">{esc(g["name"])}</span>'
            "</div>"
        )
    segs = []
    fills = []
    for s in timeline["screens"]:
        seg_class = " vseg-outro" if s["type"] == "outro" else (" vseg-cover" if s["type"] == "cover" else "")
        segs.append(
            f'<div class="vendor-seg{seg_class}" id="vseg-{s["id"]}" style="left:{s["leftPct"]:.4f}%;'
            f'width:{s["widthPct"]:.4f}%;--vc:{s["vendorColor"]}">'
            f'<i class="v-dot"></i><span class="vendor-name" id="vendor-name-{s["id"]}">{esc(s["vendor"])}</span>'
            f'<span class="v-idx">{esc(s["order"])}</span>'
            "</div>"
        )
        fills.append(
            f'<div class="seg-fill" id="fill-{s["id"]}" '
            f'style="left:{s["leftPct"]:.4f}%;width:{s["widthPct"]:.4f}%"></div>'
        )
    return f'''
<footer class="dock" id="dock">
  <div class="dock-inner">
    <div class="dock-gutter">
      <span class="g-label cat">类型</span>
      <span class="g-label vendor">厂家</span>
      <span class="g-brand">AI<br />早报</span>
    </div>
    <div class="dock-body">
      <div class="cat-row">{''.join(groups)}</div>
      <div class="vendor-row">
        <div class="active-band" id="active-band"></div>
        {''.join(segs)}
      </div>
      <div class="track">
        <div class="track-line"></div>
        {''.join(fills)}
      </div>
      <div class="playhead" id="playhead"><span class="ph-line"></span><span class="ph-dot"></span></div>
      <div class="click-ring" id="click-ring"></div>
      <div class="dock-foot"><span>新闻类型 → AI 厂家</span><span>总长 {esc(total_tc)}</span></div>
    </div>
  </div>
</footer>'''


def total_tc(total: float) -> str:
    s = int(round(total))
    return f"{s // 60:02d}:{s % 60:02d}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", default=None, choices=["qwen-local", "volcengine"])
    ap.add_argument("--speaker", default=None)
    ap.add_argument("--speed", type=float, default=1.12)
    ap.add_argument("--reuse-tts", action="store_true", help="reuse raw_*.wav when present")
    ap.add_argument("--force-tts", action="store_true", help="regenerate raw_*.wav even when present")
    ap.add_argument("--reuse-master", action="store_true", help="reuse vo_*.wav when present")
    ap.add_argument("--no-audio", action="store_true", help="only regenerate HTML/timeline")
    ap.add_argument("--no-mix", action="store_true", help="skip audio mix generation")
    ap.add_argument("--no-covers", action="store_true", help="skip 16:9 / 4:3 cover generation")
    args = ap.parse_args()

    content = json.loads((PROJ / "content.json").read_text(encoding="utf-8"))
    screens = content["screens"]
    provider = args.provider or content["meta"].get("voice_provider", "qwen-local")
    if args.force_tts:
        args.reuse_master = False
    speaker = args.speaker or content["meta"].get("voice_speaker", "Serena")
    nav = []
    total_w = sum(n["w"] for n in content["nav"])
    left = 0.0
    for n in content["nav"]:
        wp = n["w"] / total_w * 100
        nav.append({"name": n["name"], "w": n["w"], "leftPct": left, "widthPct": wp})
        left += wp

    RAW.mkdir(parents=True, exist_ok=True)
    AUDIO.mkdir(parents=True, exist_ok=True)

    if not args.no_audio:
        if args.force_tts:
            pending = screens
        elif args.reuse_tts:
            pending = [
                s for s in screens
                if (not (RAW / f"raw_{s['id']}.wav").exists())
                or (RAW / f"raw_{s['id']}.wav").stat().st_size < 4096
            ]
        else:
            pending = screens
        if pending:
            if provider == "qwen-local":
                from scripts.tts_provider import synthesize_qwen
                synthesize_qwen(pending, RAW, speaker, MODEL, force=args.force_tts)
            else:
                from scripts.tts_provider import synthesize_volcengine
                synthesize_volcengine(pending, RAW, force=args.force_tts)

    vo_paths = []
    durations = []
    for s in screens:
        raw = RAW / f"raw_{s['id']}.wav"
        vo = AUDIO / f"vo_{s['id']}.wav"
        if not raw.exists():
            raise FileNotFoundError(f"missing {raw}; run without --no-audio or provide the file")
        if args.reuse_master and vo.exists() and vo.stat().st_size > 4096:
            pass
        else:
            master_voice(raw, vo, args.speed)
        d = duration_of(vo)
        vo_paths.append(vo)
        durations.append(d)
        print(f"[vo] {s['id']:<8} {d:6.2f}s  {vo.name}")

    timeline = build_timeline(content, durations, sum(durations), nav)
    total = timeline["total"]
    (AUDIO / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")

    if not args.no_audio and not args.no_mix:
        click = AUDIO / "click.wav"
        make_click(click)
        build_mix(vo_paths, timeline["screens"], timeline["transitions"], total, click, AUDIO / "mix.wav")
        print(f"[mix] {duration_of(AUDIO / 'mix.wav'):.2f}s -> assets/audio/mix.wav")

    cats = {s["category"]: s.get("categoryColor") or CAT_FALLBACK.get(s["category"], ORANGE) for s in screens}
    order_by_id = {s["id"]: s["order"] for s in timeline["screens"]}
    for s in content["screens"]:
        s["order"] = order_by_id[s["id"]]
    template = (PROJ / "template.tpl").read_text(encoding="utf-8")
    screens_html = render_screens(content["screens"], cats)
    dock_html = render_dock(timeline, total_tc(total))
    nav_html = render_nav(timeline["nav"], content["meta"]["date"])
    html_out = (
        template
        .replace("{{DURATION}}", f"{total:.3f}")
        .replace("{{TOTAL_TC}}", total_tc(total))
        .replace("{{NAV}}", nav_html)
        .replace("{{SCREENS}}", screens_html)
        .replace("{{DOCK}}", dock_html)
        .replace("{{TIMELINE_JSON}}", json.dumps(timeline, ensure_ascii=False, separators=(",", ":")))
    )
    (PROJ / "index.html").write_text(html_out, encoding="utf-8")
    print(f"[html] duration={total:.3f}s screens={len(screens)}")
    if not args.no_covers:
        try:
            from scripts.make_covers import generate_covers
            covers = generate_covers(PROJ)
            print(f"[covers] {', '.join(p.name for p in covers)}")
        except Exception as exc:
            print(f"[covers] skipped: {type(exc).__name__}: {exc}")
    for tr in timeline["transitions"]:
        print(f"[cut] {tr['at']:6.2f}s  {tr['from']} -> {tr['to']}  click={tr['clickAt']:.2f}")


if __name__ == "__main__":
    main()
