#!/usr/bin/env python3
"""聚合每日 AI 资讯，输出可人工挑选的视频候选清单。"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

HF_NEWS = Path(__file__).resolve().parents[1]
WORKSPACE = HF_NEWS.parent
OSS = WORKSPACE / "oss"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

AI_RADAR_DAILY = "https://raw.githubusercontent.com/LearnPrompt/ai-news-radar/master/data/daily-brief.json"
AI_RADAR_STORIES = "https://raw.githubusercontent.com/LearnPrompt/ai-news-radar/master/data/stories-merged.json"
AIHOT_SELECTED = "https://aihot.virxact.com/api/public/items?mode=selected&limit=50"
FOLLOW_X = "https://raw.githubusercontent.com/zarazhangrui/follow-builders/main/feed-x.json"
FOLLOW_BLOGS = "https://raw.githubusercontent.com/zarazhangrui/follow-builders/main/feed-blogs.json"
FOLLOW_PODCASTS = "https://raw.githubusercontent.com/zarazhangrui/follow-builders/main/feed-podcasts.json"

RSS_SOURCES = [
    ("OpenAI News", "https://openai.com/news/rss.xml"),
    ("Google DeepMind", "https://deepmind.google/blog/rss.xml"),
]

OFFICIAL_DOMAINS = (
    "openai.com", "anthropic.com", "deepmind.google", "blog.google", "ai.google",
    "moonshot.ai", "moonshot.cn", "qwen.ai", "alibaba.com", "deepseek.com",
    "minimax.io", "minimax.ai", "bytedance.com", "tencent.com", "x.ai",
    "mistral.ai", "nvidia.com", "meta.com", "ai.meta.com", "huggingface.co",
    "kuaishou.com", "zhipuai.cn", "z.ai", "stepfun.com", "baidu.com",
)

VENDOR_RULES = [
    ("Kimi", ["kimi", "moonshot", "月之暗面"]),
    ("Qoder", ["qoder"]),
    ("MiniMax", ["minimax"]),
    ("Anthropic", ["anthropic", "claude"]),
    ("OpenAI", ["openai", "chatgpt", "gpt", "codex", "sora"]),
    ("Google", ["google", "deepmind", "gemini", "veo"]),
    ("Meta", ["meta", "llama"]),
    ("xAI", ["xai", "grok"]),
    ("DeepSeek", ["deepseek", "深度求索"]),
    ("Qwen", ["qwen", "通义", "alibaba", "阿里"]),
    ("ByteDance", ["bytedance", "字节", "doubao", "豆包"]),
    ("Tencent", ["tencent", "腾讯", "hunyuan", "混元"]),
    ("Kuaishou", ["kuaishou", "快手", "kling", "可灵"]),
    ("Zhipu", ["zhipu", "智谱", "glm", "z.ai"]),
    ("StepFun", ["stepfun", "阶跃"]),
    ("Mistral", ["mistral"]),
    ("Cursor", ["cursor"]),
    ("Cognition", ["cognition", "devin"]),
    ("Hugging Face", ["huggingface", "hugging face"]),
    ("NVIDIA", ["nvidia", "英伟达"]),
    ("Apple", ["apple", "苹果"]),
    ("Samsung", ["samsung", "三星"]),
    ("Baidu", ["baidu", "百度", "文心"]),
    ("Xiaomi", ["xiaomi", "小米"]),
    ("Huawei", ["huawei", "华为", "盘古"]),
    ("Runway", ["runway"]),
    ("Midjourney", ["midjourney"]),
    ("Luma", ["luma"]),
    ("Pika", ["pika"]),
    ("Vidu", ["vidu"]),
]

CATEGORY_HINT = {
    "official": "要闻",
    "industry": "要闻",
    "product": "产品应用",
    "ai-products": "产品应用",
    "ai-models": "模型发布",
    "model": "模型发布",
    "research": "前沿与传闻",
    "ai-research": "前沿与传闻",
    "opensource": "开发生态",
    "developer": "开发生态",
    "watch": "开发生态",
}

TRUST = {"official": 4, "daily": 3, "aggregator": 2, "social": 1, "builder": 1, "podcast": 0}
BASE = {"official": 3.0, "daily": 2.6, "aggregator": 1.6, "social": 1.2, "builder": 1.0, "podcast": 0.8}
TYPE_BONUS = {"要闻": 2.2, "模型发布": 2.0, "产品应用": 1.0, "开发生态": 0.7, "前沿与传闻": 0.3}

TAG_RE = re.compile(r"<[^>]+>")
TRACKING_RE = re.compile(r"^(utm_|spm$|ref$|source$|from$|share|fbclid$|gclid$)")
DIGEST_RE = re.compile(r"周报|日报|周刊|周记|速递|早报|简报|晚报|newsletter|digest|roundup|recap|weekly|daily", re.I)
OPINION_RE = re.compile(r"详解|手把手|教程|观点|评论|复盘|解读|为什么|如何|指南|玩法|实测", re.I)
MODEL_RE = re.compile(
    r"(gpt[\s-]?\d[\w.\-]*|claude[\s-]?\d[\w.\-]*|gemini[\s-]?\d[\w.\-]*|"
    r"kimi[\s-]?[\w.\-]+|qwen[\s-]?\d[\w.\-]*|deepseek[\s-]?[\w.\-]+|"
    r"minimax[\s-]?[\w.\-]+|m\d(?:\.\d+)?[\s-]?[a-z]*|kling[\s-]?\d[\w.\-]*|"
    r"llama[\s-]?\d[\w.\-]*|grok[\s-]?\d[\w.\-]*|glm[\s-]?\d[\w.\-]*|"
    r"hunyuan[\w.\-]*|doubao[\w.\-]*|seed[\s-]?\d[\w.\-]*)",
    re.I,
)


@dataclass
class Candidate:
    title: str
    url: str
    source: str
    source_kind: str
    published_at: str = ""
    summary: str = ""
    category_hint: str = ""
    source_count: int = 1
    signals: list[str] = field(default_factory=list)
    alt_sources: list[str] = field(default_factory=list)
    merged_from: list[dict] = field(default_factory=list)
    official_account: bool = False

    def __post_init__(self) -> None:
        self.title = clean_text(self.title)
        self.summary = clean_text(self.summary)
        self.url = canonical_url(self.url)
        self.source = clean_text(self.source)
        self.published_at = normalize_time(self.published_at)
        self.category_hint = CATEGORY_HINT.get(self.category_hint, self.category_hint)
        self.alt_sources = [clean_text(x) for x in self.alt_sources if clean_text(x)]
        if not self.merged_from:
            self.merged_from = [{"source": self.source, "url": self.url, "kind": self.source_kind}]

    @property
    def vendor(self) -> str:
        return detect_vendor(self.title, self.source)

    @property
    def news_type(self) -> str:
        return detect_type(self.title, self.summary, self.category_hint)

    @property
    def is_digest(self) -> bool:
        return bool(DIGEST_RE.search(self.title) or DIGEST_RE.search(self.source))

    @property
    def is_opinion(self) -> bool:
        return bool(OPINION_RE.search(self.title))

    @property
    def confidence(self) -> str:
        if self.source_kind == "official" or is_official_url(self.url):
            return "官方确认"
        if self.source_count >= 2 or len({m.get("source") for m in self.merged_from}) >= 2:
            return "多源印证"
        return "单源信号"

    @property
    def key(self) -> str:
        return title_key(self.title)

    def to_dict(self, rank: int = 0) -> dict:
        return {
            "rank": rank,
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "source_kind": self.source_kind,
            "published_at": self.published_at,
            "summary": self.summary,
            "vendor": self.vendor,
            "news_type": self.news_type,
            "confidence": self.confidence,
            "is_digest": self.is_digest,
            "is_opinion": self.is_opinion,
            "score": round(self.score(), 1),
            "source_count": max(self.source_count, len(self.merged_from)),
            "signals": self.signals,
            "alt_sources": self.alt_sources,
            "merged_from": self.merged_from,
        }

    def score(self) -> float:
        raw = BASE.get(self.source_kind, 1.0)
        raw += recency_bonus(self.published_at)
        raw += min(1.8, 0.6 * (max(self.source_count, len(self.merged_from)) - 1))
        text = f"{self.title} {self.summary}"
        if re.search(r"发布|开源|ipo|s-?1|上市|融资|收购|并购|免费|降价|突破|首个|最强|泄露|漏洞", text, re.I):
            raw += 0.9
        elif re.search(r"更新|上线|集成|api|合作|推出|支持|开放", text, re.I):
            raw += 0.4
        if self.official_account:
            raw += 0.2
        if self.confidence != "官方确认" and re.search(r"传闻|曝|据称|据悉|可能|计划|或将|未证实", text):
            raw -= 0.7
        if re.search(r"如何|案例|客户|玩法|体验", text) and not re.search(r"发布|开源|上线|推出", text):
            raw -= 0.5
        if self.source_kind == "builder" and self.vendor == "行业":
            raw -= 0.3
        if self.is_digest:
            raw -= 2.0
        if self.is_opinion:
            raw -= 1.2
        return max(0.0, min(100.0, raw / 6.5 * 100))


def clean_text(value: str) -> str:
    value = html.unescape(value or "")
    value = TAG_RE.sub(" ", value)
    return re.sub(r"\s+", " ", value).strip()


def title_key(value: str) -> str:
    value = clean_text(value).lower()
    value = re.sub(r"https?://\S+", " ", value)
    value = re.sub(r"[^\w\u4e00-\u9fff]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def canonical_url(value: str) -> str:
    if not value:
        return ""
    parts = urlsplit(value.strip())
    host = parts.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    if host in ("twitter.com", "x.com"):
        host = "x.com"
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not TRACKING_RE.match(k)]
    return urlunsplit((parts.scheme or "https", host, parts.path.rstrip("/"), urlencode(query), ""))


def is_official_url(url: str) -> bool:
    host = urlsplit(url).netloc.lower()
    return any(host == d or host.endswith("." + d) for d in OFFICIAL_DOMAINS)


def normalize_time(value: str) -> str:
    if not value:
        return ""
    value = str(value).strip()
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            dt = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_time(value: str) -> datetime | None:
    value = normalize_time(value)
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def recency_bonus(value: str) -> float:
    dt = parse_time(value)
    if not dt:
        return 0.0
    hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
    if hours < 0:
        return 0.2
    if hours <= 6:
        return 1.0
    if hours <= 12:
        return 0.6
    if hours <= 24:
        return 0.3
    if hours <= 72:
        return 0.1
    return 0.0


def key_position(text: str, key: str) -> int | None:
    if key.isascii():
        match = re.search(r"(?<![a-z0-9])" + re.escape(key) + r"(?![a-z0-9])", text)
        return match.start() if match else None
    return text.find(key) if key in text else None


def detect_vendor(*values: str) -> str:
    text = " ".join(v for v in values if v).lower()
    matches = []
    for order, (vendor, keys) in enumerate(VENDOR_RULES):
        for key in keys:
            pos = key_position(text, key)
            if pos is not None:
                matches.append((pos, order, vendor))
    return min(matches)[2] if matches else "行业"


def detect_type(title: str, summary: str, hint: str = "") -> str:
    title_has_signal = re.search(
        r"s-?1|ipo|上市|招股|融资|收购|并购|财报|营收|发布|开源|权重|模型|"
        r"论文|研究|基准|实验|突破|漏洞|攻击|渗透|对齐|红队|安全|机器人|芯片|算力|"
        r"sdk|cli|ide|编程|开发者|github|框架|工具链|mcp|agent|代码|"
        r"功能|更新|升级|app|应用|集成|订阅|定价|免费|api|插件|桌面|移动端|浏览器",
        title,
        re.I,
    )
    text = title if title_has_signal else f"{title} {summary}"
    if re.search(r"\bs-?1\b|\bipo\b|上市|招股|融资|收购|并购|估值|财报|营收|亿美元|亿元|战略合作|裁员|监管|诉讼", text, re.I):
        return "要闻"
    if re.search(r"漏洞|攻击|渗透|对齐|红队|论文|研究|基准|benchmark|实验|突破|材料|芯片|算力|数据中心|安全|机器人", text, re.I):
        return "前沿与传闻"
    model_context = re.search(r"模型|权重|checkpoint|gguf|量化|m\d|gpt|claude|gemini|kimi|qwen|deepseek|minimax|llama|grok|glm|hunyuan|doubao|kling|sora|veo", text, re.I)
    if model_context and re.search(r"发布|开源|权重|checkpoint|gguf|量化|preview|release|launch|unveil|introduc", text, re.I):
        return "模型发布"
    if re.search(r"sdk|cli|ide|编程|开发者|github|框架|工具链|mcp|部署|agent|代码|开源社区|qoder|cursor|vllm|推理|工具调用|数据引擎|数据集|wasm|rust", text, re.I):
        return "开发生态"
    if re.search(r"功能|更新|升级|app|应用|集成|订阅|定价|免费|api|插件|桌面|移动端|浏览器|上线", text, re.I):
        return "产品应用"
    return hint or "要闻"


def event_keys(text: str) -> set[str]:
    keys = {re.sub(r"\s+", "", m.group(1).lower()) for m in MODEL_RE.finditer(text)}
    if re.search(r"\bs-?1\b|\bipo\b|上市|招股", text, re.I):
        keys.add("ipo")
    if re.search(r"融资|亿美元|亿元", text, re.I):
        keys.add("funding")
    if re.search(r"收购|并购", text, re.I):
        keys.add("ma")
    return keys


def same_story(a: Candidate, b: Candidate) -> bool:
    if a.url and a.url == b.url:
        return True
    if not a.key or not b.key:
        return False
    if a.vendor != "行业" and a.vendor == b.vendor:
        shared = event_keys(f"{a.title} {a.summary}") & event_keys(f"{b.title} {b.summary}")
        if shared:
            return True
        ratio = SequenceMatcher(None, a.key, b.key).ratio()
        if ratio >= 0.72:
            return True
        shorter, longer = sorted((a.key, b.key), key=len)
        if len(shorter) >= 14 and shorter in longer:
            return True
    return False


def merge_into(primary: Candidate, other: Candidate) -> None:
    primary.source_count = max(primary.source_count, other.source_count) + 1
    primary.alt_sources.extend(other.alt_sources or [other.source])
    primary.merged_from.extend(other.merged_from)
    primary.signals.extend(other.signals)
    if not primary.summary and other.summary:
        primary.summary = other.summary
    if not primary.published_at and other.published_at:
        primary.published_at = other.published_at
    if other.confidence == "官方确认" and primary.confidence != "官方确认":
        primary.summary = primary.summary or other.summary
    seen = set()
    primary.merged_from = [
        m for m in primary.merged_from
        if not (m.get("url") in seen or seen.add(m.get("url")))
    ]


CURL = shutil.which("curl")


def fetch_bytes(url: str, timeout: int = 30) -> bytes:
    if CURL:
        base = [
            CURL, "-sSL", "--retry", "3", "--retry-delay", "1", "--max-time", str(timeout),
            "-A", UA, "-H", "Connection: close", url,
        ]
        result = subprocess.run(base + ["--ssl-no-revoke"], capture_output=True, timeout=timeout + 10)
        if result.returncode != 0:
            result = subprocess.run(base, capture_output=True, timeout=timeout + 10)
        if result.returncode != 0:
            message = result.stderr.decode("utf-8", "replace").strip()
            raise RuntimeError(message or f"curl exit {result.returncode}")
        return result.stdout
    req = Request(url, headers={"User-Agent": UA, "Connection": "close"})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_json(url: str, timeout: int = 30) -> dict:
    return json.loads(fetch_bytes(url, timeout).decode("utf-8"), strict=False)


def read_local(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"), strict=False)
    except (OSError, json.JSONDecodeError):
        return None


def load_json_with_fallback(url: str, local: Path, warnings: list[str]) -> dict | None:
    try:
        return fetch_json(url)
    except Exception as exc:
        data = read_local(local)
        if data is not None:
            warnings.append(f"{url.rsplit('/', 1)[-1]} 远端失败，改用本地克隆：{str(exc)[:120]}")
            return data
        warnings.append(f"{url.rsplit('/', 1)[-1]} 拉取失败：{str(exc)[:120]}")
        return None


def source_tier(story: dict) -> str:
    tier = story.get("source_tier")
    if not tier:
        primary = story.get("primary_item") or {}
        tier = primary.get("source_tier")
    if not tier and story.get("sources"):
        tier = story["sources"][0].get("source_tier")
    return str(tier or "").lower()


def load_ai_radar(offline: bool, warnings: list[str]) -> list[Candidate]:
    if offline:
        daily = read_local(OSS / "ai-news-radar" / "data" / "daily-brief.json")
        stories = read_local(OSS / "ai-news-radar" / "data" / "stories-merged.json")
    else:
        daily = load_json_with_fallback(AI_RADAR_DAILY, OSS / "ai-news-radar" / "data" / "daily-brief.json", warnings)
        stories = load_json_with_fallback(AI_RADAR_STORIES, OSS / "ai-news-radar" / "data" / "stories-merged.json", warnings)
    if not stories:
        return []
    daily_ids = {x.get("story_id") for x in (daily or {}).get("items", []) if x.get("story_id")}
    daily_urls = {canonical_url(x.get("url", "")) for x in (daily or {}).get("items", [])}
    out = []
    for story in stories.get("stories", []):
        primary = story.get("primary_item") or {}
        url = story.get("primary_url") or story.get("url") or primary.get("url", "")
        if not url:
            continue
        tier = source_tier(story)
        in_daily = story.get("story_id") in daily_ids or canonical_url(url) in daily_urls
        kind = "official" if tier == "official" else ("daily" if in_daily else "aggregator")
        title = primary.get("title_zh") or story.get("title") or primary.get("title") or ""
        summary = primary.get("recommend_reason_zh") or primary.get("summary") or story.get("title") or ""
        out.append(Candidate(
            title=title,
            url=url,
            source=story.get("source") or story.get("source_name") or "ai-news-radar",
            source_kind=kind,
            published_at=story.get("latest_at") or primary.get("published_at") or story.get("earliest_at", ""),
            summary=summary,
            category_hint=story.get("category", ""),
            source_count=max(1, int(story.get("source_count") or 1)),
            signals=list(story.get("reasons") or []),
            alt_sources=list(story.get("source_names") or []),
        ))
    return out


def load_aihot(warnings: list[str]) -> list[Candidate]:
    try:
        data = fetch_json(AIHOT_SELECTED)
    except Exception as exc:
        warnings.append(f"AI HOT 拉取失败：{type(exc).__name__}")
        return []
    out = []
    for item in data.get("items", []):
        source = item.get("source") or "AI HOT"
        kind = "official" if is_official_url(item.get("url", "")) else ("social" if source.startswith("X：") else "aggregator")
        official_account = source.startswith("X：") and detect_vendor(source) != "行业"
        out.append(Candidate(
            title=item.get("title") or "",
            url=item.get("url") or item.get("permalink") or "",
            source=source,
            source_kind=kind,
            published_at=item.get("publishedAt") or "",
            summary=item.get("summary") or "",
            category_hint=item.get("category") or "",
            signals=[f"aihot_score:{item.get('score')}"] if item.get("score") is not None else [],
            official_account=official_account,
        ))
    return out


def load_follow_builders(offline: bool, warnings: list[str]) -> list[Candidate]:
    paths = {
        "x": OSS / "follow-builders" / "feed-x.json",
        "blogs": OSS / "follow-builders" / "feed-blogs.json",
        "podcasts": OSS / "follow-builders" / "feed-podcasts.json",
    }
    urls = {"x": FOLLOW_X, "blogs": FOLLOW_BLOGS, "podcasts": FOLLOW_PODCASTS}
    data = {}
    for key in paths:
        data[key] = read_local(paths[key]) if offline else load_json_with_fallback(urls[key], paths[key], warnings)
    out = []
    for builder in (data.get("x") or {}).get("x", []):
        name = builder.get("name") or builder.get("handle") or "Builder"
        handle = builder.get("handle") or ""
        for tweet in builder.get("tweets", []):
            text = clean_text(tweet.get("text") or "")
            if not text:
                continue
            out.append(Candidate(
                title=text[:120],
                url=tweet.get("url") or "",
                source=f"{name} (@{handle})" if handle else name,
                source_kind="builder",
                published_at=tweet.get("createdAt") or "",
                summary=text,
                category_hint="developer",
                signals=["follow-builders"],
            ))
    for blog in (data.get("blogs") or {}).get("blogs", []):
        name = blog.get("name") or blog.get("source") or "Blog"
        kind = "official" if "anthropic" in name.lower() or "claude" in name.lower() else "builder"
        out.append(Candidate(
            title=blog.get("title") or "",
            url=blog.get("url") or "",
            source=name,
            source_kind=kind,
            published_at=blog.get("publishedAt") or "",
            summary=blog.get("summary") or blog.get("description") or "",
            category_hint="official",
            signals=["follow-builders:blog"],
        ))
    for pod in (data.get("podcasts") or {}).get("podcasts", []):
        out.append(Candidate(
            title=pod.get("title") or "",
            url=pod.get("url") or "",
            source=f"{pod.get('name', 'Podcast')} (podcast)",
            source_kind="podcast",
            published_at=pod.get("publishedAt") or "",
            summary=(pod.get("transcript") or "")[:500],
            category_hint="research",
            signals=["follow-builders:podcast"],
        ))
    return out


def parse_feed(raw: bytes) -> list[dict]:
    if len(raw) > 3_000_000:
        raise ValueError("feed too large")
    upper = raw.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise ValueError("DTD/entity in feed is not allowed")
    raw = bytes(b for b in raw if b in (9, 10, 13) or b >= 32)
    root = ET.fromstring(raw)
    entries = []
    for node in root.iter():
        tag = node.tag.split("}")[-1]
        if tag not in ("item", "entry"):
            continue
        values = {}
        for child in list(node):
            ctag = child.tag.split("}")[-1]
            text = clean_text("".join(child.itertext()))
            if ctag == "link" and not text and child.attrib.get("href"):
                text = child.attrib["href"]
            values.setdefault(ctag, text)
        entries.append(values)
    return entries


def load_official_rss(warnings: list[str], hours: int = 72) -> list[Candidate]:
    out = []
    for name, url in RSS_SOURCES:
        try:
            entries = parse_feed(fetch_bytes(url))
        except Exception as exc:
            warnings.append(f"{name} RSS 失败：{type(exc).__name__}")
            continue
        for entry in entries:
            published = entry.get("pubDate") or entry.get("published") or entry.get("updated") or ""
            dt = parse_time(published)
            if dt and (datetime.now(timezone.utc) - dt).total_seconds() > hours * 3600:
                continue
            link = entry.get("link") or entry.get("id") or ""
            title = entry.get("title") or ""
            if not link or not title:
                continue
            out.append(Candidate(
                title=title,
                url=link,
                source=name,
                source_kind="official",
                published_at=published,
                summary=entry.get("description") or entry.get("summary") or entry.get("content") or "",
                signals=["official-rss"],
            ))
    return out


def dedupe(candidates: list[Candidate]) -> list[Candidate]:
    candidates.sort(key=lambda c: (-TRUST.get(c.source_kind, 0), -c.score()))
    clusters: list[Candidate] = []
    for cand in candidates:
        for primary in clusters:
            if same_story(primary, cand):
                merge_into(primary, cand)
                break
        else:
            clusters.append(cand)
    return clusters


def pick_recommended(cands: list[Candidate], count: int = 5) -> list[Candidate]:
    clean = [c for c in cands if not c.is_digest and not c.is_opinion]
    pool = [c for c in clean if c.confidence != "单源信号" or c.official_account] or clean or cands
    if not pool:
        return []
    cover_pool = [c for c in pool if c.news_type in ("要闻", "模型发布")] or pool
    cover = max(cover_pool, key=lambda c: (c.score(), c.confidence == "官方确认"))
    selected = [cover]
    while len(selected) < count:
        used_vendors = {c.vendor for c in selected}
        used_types = {c.news_type for c in selected}
        rest = [c for c in pool if c not in selected]
        if not rest:
            break
        fresh_vendors = [c for c in rest if c.vendor not in used_vendors]
        if fresh_vendors:
            rest = fresh_vendors
        nxt = max(
            rest,
            key=lambda c: c.score()
            + TYPE_BONUS.get(c.news_type, 0.0)
            + (2.0 if c.news_type not in used_types else 0.0)
            + (1.0 if c.confidence == "官方确认" else 0.0)
            + (0.5 if c.official_account else 0.0),
        )
        selected.append(nxt)
    return selected


def render_markdown(report: dict) -> str:
    lines = [
        f"# {report['date']} AI 早报候选",
        "",
        f"- 生成时间：{report['generated_at']}",
        f"- 数据源：{report['source_summary']}",
        "",
        f"## 推荐上片（{len(report['recommended'])} 条）",
        "",
        "| # | 类型 | 厂家 | 标题 | 可信度 | 来源 |",
        "|---|---|---|---|---|---|",
    ]
    for index, item in enumerate(report["recommended"], 1):
        lines.append(
            f"| {index} | {item['news_type']} | {item['vendor']} | "
            f"{item['title'].replace('|', '/')} | {item['confidence']} | {item['source'].replace('|', '/')} |"
        )
    lines += ["", "## 候选池 Top", ""]
    lines += ["| # | 分数 | 类型 | 厂家 | 标题 | 可信度 | 来源 |", "|---|---|---|---|---|---|---|"]
    for item in report["top"]:
        lines.append(
            f"| {item['rank']} | {item['score']} | {item['news_type']} | {item['vendor']} | "
            f"{item['title'].replace('|', '/')} | {item['confidence']} | {item['source'].replace('|', '/')} |"
        )
    if report["warnings"]:
        lines += ["", "## 采集告警", ""]
        lines += [f"- {w}" for w in report["warnings"]]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="聚合每日 AI 资讯，输出视频候选清单")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"), help="报告日期")
    parser.add_argument("--top", type=int, default=20, help="候选池条数")
    parser.add_argument("--recommend", type=int, default=8, help="推荐上片条数，不按视频时长截断")
    parser.add_argument("--offline", action="store_true", help="只读本地克隆数据")
    parser.add_argument("--no-rss", action="store_true", help="跳过官方 RSS 直连")
    parser.add_argument("--out-dir", default=str(HF_NEWS / "out" / "daily"), help="输出目录")
    args = parser.parse_args()

    warnings: list[str] = []
    tasks = {
        "radar": (load_ai_radar, (args.offline, warnings)),
        "aihot": (load_aihot, (warnings,)),
        "builders": (load_follow_builders, (args.offline, warnings)),
    }
    if not args.no_rss:
        tasks["rss"] = (load_official_rss, (warnings,))

    results: dict[str, list[Candidate]] = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(fn, *kwargs): name for name, (fn, kwargs) in tasks.items()}
        for future in as_completed(futures):
            name = futures[future]
            try:
                results[name] = future.result()
            except Exception as exc:
                warnings.append(f"{name} 采集失败：{type(exc).__name__}: {exc}")
                results[name] = []

    radar = results.get("radar", [])
    aihot = results.get("aihot", [])
    builders = results.get("builders", [])
    rss = results.get("rss", [])
    candidates: list[Candidate] = radar + aihot + builders + rss
    radar_count = len(radar)

    merged = dedupe(candidates)
    merged.sort(key=lambda c: -c.score())
    top = merged[: args.top]
    recommended = pick_recommended(merged, args.recommend)

    x_count = len([c for c in builders if "follow-builders" in c.signals])
    blog_count = len([c for c in builders if "follow-builders:blog" in c.signals])
    podcast_count = len([c for c in builders if "follow-builders:podcast" in c.signals])
    source_summary = (
        f"ai-news-radar {radar_count} 条 / AI HOT {len(aihot)} 条 / "
        f"follow-builders X {x_count} 条、博客 {blog_count} 条、播客 {podcast_count} 条 / "
        f"官方 RSS {len(rss)} 条；去重后 {len(merged)} 条"
    )
    report = {
        "date": args.date,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_summary": source_summary,
        "warnings": warnings,
        "recommended": [c.to_dict(i + 1) for i, c in enumerate(recommended)],
        "top": [c.to_dict(i + 1) for i, c in enumerate(top)],
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"candidates-{args.date}.json"
    md_path = out_dir / f"candidates-{args.date}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(f"候选池：{len(merged)} 条，推荐 {len(recommended)} 条")
    print(source_summary)
    print("\n推荐上片：")
    for index, item in enumerate(report["recommended"], 1):
        print(f"{index}. [{item['news_type']} / {item['vendor']} / {item['confidence']}] {item['title']}")
        print(f"   {item['url']}")
    print(f"\nJSON: {json_path}")
    print(f"MD:   {md_path}")
    if warnings:
        print("\n告警：")
        for warning in warnings:
            print(f"- {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
