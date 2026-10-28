#!/usr/bin/env python3
"""把 AI 早报成片投稿到 B 站，并加入指定合集小节。

默认 dry-run，只打印参数；加 --execute 才真正上传。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

DEFAULT_TAGS = ["AI", "人工智能", "科技资讯"]


def resolve_biliup(project: Path, explicit: str | None) -> Path | None:
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    env = os.environ.get("BILIUP_BIN")
    if env:
        candidates.append(Path(env))
    candidates += [
        project.parent / "tools" / "bin" / "biliup" / "biliup.exe",
        project.parent / "tools" / "bin" / "biliup.exe",
    ]
    found = shutil.which("biliup")
    if found:
        candidates.append(Path(found))
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def latest_video(project: Path) -> Path | None:
    videos = sorted((project / "out").glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    return videos[0] if videos else None


def format_ts(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    return f"{total // 60:02d}:{total % 60:02d}"


def build_desc(content: dict, project: Path) -> str:
    screens = content["screens"]
    cover = screens[0]
    stories = [s for s in screens if s.get("type") == "story"]
    lines = [f"{len(stories)} 条 AI 要闻，每条附原文截图。", ""]
    timeline_path = project / "assets" / "audio" / "timeline.json"
    times = {}
    if timeline_path.exists():
        timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
        times = {s["id"]: s.get("segStart", s.get("voiceStart", 0)) for s in timeline.get("screens", [])}
    lines.append(f"{format_ts(0)} 封面")
    for story in stories:
        start = times.get(story["id"], 0)
        lines.append(f"{format_ts(start)} {story.get('title', '')}")
    sources = []
    for story in stories:
        evidence = story.get("evidence") or {}
        source = evidence.get("source") or ""
        if source and source not in sources:
            sources.append(source)
    if sources:
        lines += ["", "来源：" + "、".join(sources)]
    if cover.get("caption"):
        lines += ["", cover["caption"]]
    return "\n".join(lines)


def build_title(content: dict) -> str:
    meta = content.get("meta", {})
    cover = content["screens"][0]
    title = meta.get("publish_title") or cover.get("title") or "AI 早报"
    issue = meta.get("issue") or meta.get("date") or ""
    if issue and "AI 早报" not in title:
        title = f"{title}｜AI 早报 {issue}"
    return title[:80]


def build_tags(content: dict) -> str:
    tags = list(DEFAULT_TAGS)
    for story in content["screens"]:
        if story.get("type") != "story":
            continue
        vendor = story.get("vendor")
        if vendor and vendor not in tags and vendor != "行业":
            tags.append(vendor)
    return ",".join(tags[:10])


def validate_cover(path: Path) -> str | None:
    if not path.exists():
        return f"封面不存在：{path}"
    if path.stat().st_size > 5 * 1024 * 1024:
        return "封面超过 5MB"
    try:
        image = Image.open(path)
    except Exception as exc:
        return f"封面无法读取：{exc}"
    width, height = image.size
    if width < 1146 or height < 717:
        return f"封面尺寸过小：{width}x{height}，B 站要求至少 1146x717"
    ratio = width / height
    if abs(ratio - 16 / 9) > 0.03:
        return f"封面不是 16:9：{width}x{height}"
    return None


def cmd_text(cmd: list[str]) -> str:
    return subprocess.list2cmdline(cmd)


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def parse_bvid(output: str) -> str | None:
    match = re.search(r'BV[0-9A-Za-z]{10}', output)
    return match.group(0) if match else None


def main() -> int:
    parser = argparse.ArgumentParser(description="B 站投稿并加入合集（默认 dry-run）")
    parser.add_argument("--project", default=".", help="AI 早报工程目录")
    parser.add_argument("--video", default=None, help="视频路径，默认 out/ 下最新 mp4")
    parser.add_argument("--cover", default=None, help="16:9 封面，默认 out/covers/cover_16x9.jpg")
    parser.add_argument("--title", default=None, help="标题，默认取 content.json")
    parser.add_argument("--desc", default=None, help="简介，默认按 content/timeline 生成")
    parser.add_argument("--tags", default=None, help="逗号分隔标签，默认按内容生成")
    parser.add_argument("--tid", type=int, default=231, help="分区，默认 231 计算机技术")
    parser.add_argument("--copyright", type=int, default=1, choices=[1, 2], help="1 自制 2 转载")
    parser.add_argument("--dynamic", default="", help="空间动态")
    parser.add_argument("--cookie", default=os.environ.get("BILIBILI_COOKIE", ""), help="biliup cookies 文件")
    parser.add_argument("--biliup", default=None, help="biliup 可执行文件")
    parser.add_argument("--season-id", type=int, default=None, help="合集 ID，见 biliup season list")
    parser.add_argument("--section-id", type=int, default=None, help="小节 ID")
    parser.add_argument("--skip-season", action="store_true", help="不加入合集")
    parser.add_argument("--execute", action="store_true", help="真正上传；不加则 dry-run")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    content_path = project / "content.json"
    if not content_path.exists():
        print(f"[fail] 找不到 {content_path}")
        return 1
    content = json.loads(content_path.read_text(encoding="utf-8"))

    video = Path(args.video) if args.video else latest_video(project)
    cover = Path(args.cover) if args.cover else project / "out" / "covers" / "cover_16x9.jpg"
    if not video or not video.exists():
        print("[fail] 找不到视频，用 --video 指定")
        return 1
    cover_error = validate_cover(cover)
    if cover_error:
        print(f"[fail] {cover_error}")
        return 1
    title = (args.title or build_title(content))[:80]
    desc = args.desc or build_desc(content, project)
    tags = args.tags or build_tags(content)
    if len(tags.split(",")) > 10:
        print("[fail] 标签超过 10 个")
        return 1

    biliup = resolve_biliup(project, args.biliup)
    if not biliup:
        print("[fail] 找不到 biliup，设置 BILIUP_BIN 或 --biliup")
        return 1
    cookie = Path(args.cookie) if args.cookie else None
    if args.execute and (not cookie or not cookie.exists()):
        print("[fail] 缺少有效 cookie 文件；先运行 biliup login")
        return 1
    if not args.skip_season and (not args.season_id or not args.section_id):
        print("[fail] 需要 --season-id 和 --section-id（或用 --skip-season）；先运行 biliup season list")
        return 1

    upload_cmd = [
        str(biliup),
        "-u", str(cookie or "<COOKIE>"),
        "upload", str(video),
        "--title", title,
        "--desc", desc,
        "--tid", str(args.tid),
        "--tag", tags,
        "--cover", str(cover),
        "--copyright", str(args.copyright),
    ]
    if args.dynamic:
        upload_cmd += ["--dynamic", args.dynamic]
    season_cmd = None
    if not args.skip_season:
        season_cmd = [
            str(biliup), "-u", str(cookie or "<COOKIE>"),
            "season", "add", "--vid", "<BV>", str(args.section_id),
        ]

    print("[title]", title)
    print("[cover]", cover)
    print("[video]", video)
    print("[tags]", tags)
    print("[desc]")
    print(desc)
    print("[upload]")
    print(cmd_text(upload_cmd))
    if season_cmd:
        print("[season]")
        print(cmd_text(season_cmd))

    if not args.execute:
        print("[dry-run] 未上传；确认后加 --execute")
        return 0

    print("[run] 上传中……", flush=True)
    uploaded = run(upload_cmd)
    print(uploaded.stdout[-4000:])
    if uploaded.returncode != 0:
        print(uploaded.stderr[-2000:], file=sys.stderr)
        print("[fail] 上传失败")
        return 1
    bvid = parse_bvid(uploaded.stdout + "\n" + uploaded.stderr)
    if not bvid:
        print("[fail] 上传结束但没解析到 BV 号，请检查 biliup 输出")
        return 1
    print(f"[ok] BV={bvid}  https://www.bilibili.com/video/{bvid}")

    season_ok = True
    if season_cmd:
        season_cmd[season_cmd.index("<BV>")] = bvid
        print("[run] 加入合集……", flush=True)
        attached = run(season_cmd)
        print(attached.stdout[-2000:])
        if attached.returncode != 0:
            season_ok = False
            print(attached.stderr[-2000:], file=sys.stderr)
            print("[warn] 稿件已发布，但加入合集失败；请手动 season add")
        else:
            print("[ok] 已加入合集")
    log = {
        "published_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "bvid": bvid,
        "url": f"https://www.bilibili.com/video/{bvid}",
        "title": title,
        "tid": args.tid,
        "tags": tags,
        "season_id": args.season_id,
        "section_id": args.section_id,
        "video": str(video),
        "cover": str(cover),
        "season_ok": season_ok,
    }
    log_path = project / "out" / f"publish-{bvid}.json"
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[log] {log_path}")
    return 0 if season_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())