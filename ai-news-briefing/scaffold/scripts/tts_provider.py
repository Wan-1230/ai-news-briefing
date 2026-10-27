"""TTS provider adapters.

Default: local Qwen3-TTS CustomVoice (Apache-2.0), CPU.
Optional: Volcengine TTS HTTP API for the voice the user asked for
(云晓辰-知性). The exact voice_type must come from the Volcengine console;
this project cannot guess or borrow someone else's credential.
"""
from __future__ import annotations

import base64
import json
import os
import urllib.request
import uuid
from pathlib import Path


def synthesize_qwen(rows, out_dir: Path, speaker: str, model_dir: Path, language: str = "Auto", force: bool = False) -> None:
    import soundfile as sf
    import torch
    from qwen_tts import Qwen3TTSModel

    out_dir.mkdir(parents=True, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = Qwen3TTSModel.from_pretrained(
        str(model_dir), device_map=device, dtype=torch.float32
    )
    for row in rows:
        out = out_dir / f"raw_{row['id']}.wav"
        if out.exists() and out.stat().st_size > 4096 and not force:
            print(f"[tts] reuse {out.name}")
            continue
        wavs, sr = model.generate_custom_voice(
            text=row["narration"], language=language, speaker=speaker
        )
        sf.write(str(out), wavs[0], sr)
        print(f"[tts] {row['id']}: {len(wavs[0]) / sr:.2f}s -> {out.name}")


def synthesize_volcengine(rows, out_dir: Path, force: bool = False) -> None:
    """Volcengine TTS v1. Requires VOLC_TTS_APPID/TOKEN/VOICE_TYPE.

    The voice_type for 云晓辰-知性 is copied from the user's console; it is
    intentionally not hard-coded because the public docs and the 剪映 voice
    shelf do not expose the same identifier.
    """
    appid = os.environ.get("VOLC_TTS_APPID")
    token = os.environ.get("VOLC_TTS_TOKEN")
    voice_type = os.environ.get("VOLC_VOICE_TYPE")
    cluster = os.environ.get("VOLC_TTS_CLUSTER", "volcano_tts")
    missing = [
        name
        for name, value in (
            ("VOLC_TTS_APPID", appid),
            ("VOLC_TTS_TOKEN", token),
            ("VOLC_VOICE_TYPE", voice_type),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            "Volcengine TTS needs " + ", ".join(missing) +
            "; use --provider qwen-local for the offline fallback."
        )

    url = "https://openspeech.bytedance.com/api/v1/tts"
    out_dir.mkdir(parents=True, exist_ok=True)
    for row in rows:
        out = out_dir / f"raw_{row['id']}.wav"
        if out.exists() and out.stat().st_size > 4096 and not force:
            print(f"[tts] reuse {out.name}")
            continue
        payload = {
            "app": {"appid": appid, "token": token, "cluster": cluster},
            "user": {"uid": "hf-news"},
            "audio": {
                "voice_type": voice_type,
                "encoding": "wav",
                "speed_ratio": 1.0,
                "rate": 48000,
            },
            "request": {
                "reqid": str(uuid.uuid4()),
                "text": row["narration"],
                "operation": "query",
            },
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer; {token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        if body.get("code") not in (0, 3000, None):
            raise RuntimeError(f"Volcengine TTS error: {body}")
        data = body.get("data")
        if not data:
            raise RuntimeError(f"Volcengine TTS returned no audio: {body}")
        out.write_bytes(base64.b64decode(data))
        print(f"[tts] {row['id']}: {out.stat().st_size} bytes -> {out.name}")
