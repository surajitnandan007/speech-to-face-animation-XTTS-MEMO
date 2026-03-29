from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]


def _load_env_file() -> None:
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)


def _resolve_path(raw_value: str | None, default: Optional[Path] = None) -> Optional[Path]:
    if raw_value is None:
        return default
    normalized = raw_value.strip()
    if not normalized:
        return default
    path = Path(normalized).expanduser()
    if not path.is_absolute():
        path = (BASE_DIR / path).resolve()
    else:
        path = path.resolve()
    return path


def _env_path(name: str, default: Optional[Path] = None) -> Optional[Path]:
    return _resolve_path(os.getenv(name), default)


def _env_text(name: str, default: str) -> str:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    normalized = raw_value.strip()
    return normalized or default


@dataclass(slots=True)
class AppConfig:
    memo_repo_path: Path
    memo_python_executable: str
    memo_config_path: Path
    memo_model_dir: Path
    memo_misc_model_dir: Path
    xtts_model_name: str
    xtts_model_dir: Path
    default_source_image: Optional[Path]
    default_speaker_wav: Optional[Path]
    upload_dir: Path
    results_dir: Path


def load_config() -> AppConfig:
    _load_env_file()

    base_storage = BASE_DIR / "storage"
    default_python = BASE_DIR / ".venv" / "Scripts" / "python.exe"
    return AppConfig(
        memo_repo_path=_env_path("MEMO_REPO_PATH", BASE_DIR / "memo_upstream") or (BASE_DIR / "memo_upstream"),
        memo_python_executable=_env_text(
            "MEMO_PYTHON_EXECUTABLE",
            str(default_python if default_python.exists() else sys.executable),
        ),
        memo_config_path=_env_path("MEMO_CONFIG_PATH", BASE_DIR / "configs" / "memo_inference.yaml")
        or (BASE_DIR / "configs" / "memo_inference.yaml"),
        memo_model_dir=_env_path("MEMO_MODEL_DIR", BASE_DIR / "models" / "memo") or (BASE_DIR / "models" / "memo"),
        memo_misc_model_dir=_env_path("MEMO_MISC_MODEL_DIR", BASE_DIR / "models" / "memo_misc")
        or (BASE_DIR / "models" / "memo_misc"),
        xtts_model_name=_env_text(
            "XTTS_MODEL_NAME",
            "tts_models/multilingual/multi-dataset/xtts_v2",
        ),
        xtts_model_dir=_env_path("XTTS_MODEL_DIR", BASE_DIR / "models" / "xtts_v2")
        or (BASE_DIR / "models" / "xtts_v2"),
        default_source_image=_env_path("DEFAULT_SOURCE_IMAGE"),
        default_speaker_wav=_env_path("DEFAULT_SPEAKER_WAV"),
        upload_dir=_env_path("UPLOAD_DIR", base_storage / "uploads") or (base_storage / "uploads"),
        results_dir=_env_path("RESULTS_DIR", base_storage / "results") or (base_storage / "results"),
    )
