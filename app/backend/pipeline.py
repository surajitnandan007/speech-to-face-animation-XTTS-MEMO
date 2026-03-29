from __future__ import annotations

import uuid
from pathlib import Path

from .config import AppConfig
from .memo_service import MemoService
from .models import GenerationOptions, PipelineResult
from .xtts_service import XttsService


class TalkingHeadPipeline:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.xtts = XttsService(config)
        self.memo = MemoService(config)

    def run(
        self,
        *,
        text: str | None,
        audio_path: Path | None,
        source_image: Path | None,
        speaker_wav: Path | None,
        output_dir: Path | None,
        options: GenerationOptions,
    ) -> PipelineResult:
        resolved_source = source_image or self.config.default_source_image
        if resolved_source is None:
            raise ValueError("Provide --source-image or set DEFAULT_SOURCE_IMAGE in .env.")

        resolved_output_dir = (output_dir or (self.config.results_dir / uuid.uuid4().hex[:12])).resolve()
        resolved_output_dir.mkdir(parents=True, exist_ok=True)

        used_tts = False
        resolved_audio_path: Path
        resolved_speaker = speaker_wav or self.config.default_speaker_wav
        if text:
            if resolved_speaker is None:
                raise ValueError("Provide --speaker-wav or set DEFAULT_SPEAKER_WAV when using --text.")
            used_tts = True
            resolved_audio_path = self.xtts.synthesize_wav_from_text(
                text=text,
                output_path=resolved_output_dir / "xtts.wav",
                speaker_wav=resolved_speaker,
                language=options.language,
            )
        elif audio_path:
            resolved_audio_path = audio_path.resolve()
        else:
            raise ValueError("Provide either --text or --audio-path.")

        video_path = self.memo.generate(
            audio_file=resolved_audio_path,
            source_image=resolved_source.resolve(),
            output_dir=resolved_output_dir,
            options=options,
        )
        return PipelineResult(
            audio_path=resolved_audio_path,
            source_image_path=resolved_source.resolve(),
            video_path=video_path,
            logs="XTTS + MEMO pipeline completed successfully.",
            used_tts=used_tts,
            speaker_wav_path=resolved_speaker.resolve() if resolved_speaker else None,
        )

