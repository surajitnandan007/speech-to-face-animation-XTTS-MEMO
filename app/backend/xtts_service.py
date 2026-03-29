from __future__ import annotations

from pathlib import Path

from .config import AppConfig
from .exceptions import ConfigurationError


class XttsService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._tts = None

    def synthesize_wav_from_text(
        self,
        *,
        text: str,
        output_path: Path,
        speaker_wav: Path,
        language: str,
    ) -> Path:
        clean_text = text.replace("**", "").replace("*", "").strip()
        if not clean_text:
            raise ValueError("Provide non-empty text for speech synthesis.")
        if not speaker_wav.exists():
            raise ValueError(f"Speaker wav does not exist: {speaker_wav}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        tts = self._get_tts()
        tts.tts_to_file(
            text=clean_text,
            speaker_wav=str(speaker_wav),
            language=language,
            file_path=str(output_path),
        )
        if not output_path.exists():
            raise RuntimeError("XTTS finished without creating the output wav file.")
        return output_path

    def _get_tts(self):
        if self._tts is None:
            try:
                from TTS.api import TTS
            except ModuleNotFoundError as exc:  # pragma: no cover - external runtime issue
                raise ConfigurationError(
                    "XTTS runtime is not installed. Run scripts/install_xtts_runtime.ps1 after installing Microsoft C++ Build Tools."
                ) from exc
            try:
                self._tts = TTS(self.config.xtts_model_name)
            except Exception as exc:  # pragma: no cover - external runtime issue
                raise ConfigurationError(
                    f"Failed to initialize XTTS model {self.config.xtts_model_name}."
                ) from exc
        return self._tts
