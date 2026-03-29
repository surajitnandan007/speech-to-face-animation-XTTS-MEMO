from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.backend.config import load_config
from app.backend.pipeline import TalkingHeadPipeline
from app.backend.models import GenerationOptions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the XTTS + MEMO talking-face pipeline.")
    parser.add_argument("--text", type=str, default="")
    parser.add_argument("--audio-path", type=Path)
    parser.add_argument("--source-image", type=Path)
    parser.add_argument("--speaker-wav", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--language", type=str, default="en")
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pipeline = TalkingHeadPipeline(load_config())
    try:
        result = pipeline.run(
            text=args.text.strip() or None,
            audio_path=args.audio_path,
            source_image=args.source_image,
            speaker_wav=args.speaker_wav,
            output_dir=args.output_dir,
            options=GenerationOptions(language=args.language, seed=args.seed),
        )
    except Exception as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, indent=2))
        return 1

    print(
        json.dumps(
            {
                "status": "completed",
                "audio_path": str(result.audio_path),
                "source_image_path": str(result.source_image_path),
                "video_path": str(result.video_path),
                "speaker_wav_path": str(result.speaker_wav_path) if result.speaker_wav_path else None,
                "used_tts": result.used_tts,
                "logs": result.logs,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

