from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(slots=True)
class GenerationOptions:
    language: str = "en"
    seed: int = 42


@dataclass(slots=True)
class PipelineResult:
    audio_path: Path
    source_image_path: Path
    video_path: Path
    logs: str
    used_tts: bool
    speaker_wav_path: Optional[Path] = None

