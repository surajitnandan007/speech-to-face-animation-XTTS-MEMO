from __future__ import annotations

import uuid
import traceback
from pathlib import Path
from typing import Any

import runpod

from app.backend.config import load_config
from app.backend.exceptions import ConfigurationError, GenerationError
from app.backend.models import GenerationOptions
from app.backend.pipeline import TalkingHeadPipeline
from app.worker.io_utils import encode_file_to_base64, infer_suffix, materialize_input_file


CONFIG = load_config()
PIPELINE = TalkingHeadPipeline(CONFIG)


def _parse_options(job_input: dict[str, Any]) -> GenerationOptions:
    options_input = job_input.get("options") or {}
    return GenerationOptions(
        language=str(options_input.get("language", job_input.get("language", "en"))),
        seed=int(options_input.get("seed", job_input.get("seed", 42))),
    )


def _materialize_audio(job_input: dict[str, Any]) -> Path | None:
    return materialize_input_file(
        path_value=job_input.get("audio_path"),
        url_value=job_input.get("audio_url"),
        base64_value=job_input.get("audio_base64"),
        suffix=".wav",
        label="audio",
    )


def _materialize_source_image(job_input: dict[str, Any]) -> Path | None:
    return materialize_input_file(
        path_value=job_input.get("source_image_path"),
        url_value=job_input.get("source_image_url"),
        base64_value=job_input.get("source_image_base64"),
        suffix=infer_suffix(
            path_value=job_input.get("source_image_path"),
            url_value=job_input.get("source_image_url"),
            fallback_suffix=".png",
        ),
        label="source_image",
    )


def _materialize_speaker_wav(job_input: dict[str, Any]) -> Path | None:
    return materialize_input_file(
        path_value=job_input.get("speaker_wav_path"),
        url_value=job_input.get("speaker_wav_url"),
        base64_value=job_input.get("speaker_wav_base64"),
        suffix=".wav",
        label="speaker_wav",
    )


def handler(job: dict[str, Any]) -> dict[str, Any]:
    job_input = job.get("input", {})
    text_input = (job_input.get("text") or "").strip()

    try:
        audio_path = _materialize_audio(job_input)
        source_image_path = _materialize_source_image(job_input)
        speaker_wav_path = _materialize_speaker_wav(job_input)

        result = PIPELINE.run(
            text=text_input or None,
            audio_path=audio_path,
            source_image=source_image_path,
            speaker_wav=speaker_wav_path,
            output_dir=CONFIG.results_dir / uuid.uuid4().hex[:12],
            options=_parse_options(job_input),
        )
    except (ConfigurationError, GenerationError, RuntimeError, ValueError) as exc:
        return {
            "status": "error",
            "message": str(exc),
            "logs": getattr(exc, "logs", "") or traceback.format_exc(),
        }

    response: dict[str, Any] = {
        "status": "completed",
        "audio_path": str(result.audio_path),
        "source_image_path": str(result.source_image_path),
        "video_path": str(result.video_path),
        "speaker_wav_path": str(result.speaker_wav_path) if result.speaker_wav_path else None,
        "used_tts": result.used_tts,
        "logs": result.logs,
    }

    if bool(job_input.get("return_video_base64", False)):
        response["video_base64"] = encode_file_to_base64(result.video_path)

    return response


runpod.serverless.start({"handler": handler})
