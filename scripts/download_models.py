from __future__ import annotations

import sys
from pathlib import Path

import imageio_ffmpeg
from huggingface_hub import hf_hub_download, snapshot_download

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.backend.config import load_config


FACE_MODELS = [
    "1k3d68.onnx",
    "2d106det.onnx",
    "face_landmarker_v2_with_blendshapes.task",
    "genderage.onnx",
    "glintr100.onnx",
    "scrfd_10g_bnkps.onnx",
]


def download_memo_models(config_path: Path, misc_model_dir: Path) -> None:
    snapshot_download(
        repo_id="memoavatar/memo",
        local_dir=str(config_path),
        local_dir_use_symlinks=False,
    )

    face_dir = misc_model_dir / "misc" / "face_analysis" / "models"
    face_dir.mkdir(parents=True, exist_ok=True)
    for filename in FACE_MODELS:
        hf_hub_download(
            repo_id="memoavatar/memo",
            filename=f"misc/face_analysis/models/{filename}",
            local_dir=str(misc_model_dir),
            local_dir_use_symlinks=False,
        )

    hf_hub_download(
        repo_id="memoavatar/memo",
        filename="misc/vocal_separator/Kim_Vocal_2.onnx",
        local_dir=str(misc_model_dir),
        local_dir_use_symlinks=False,
    )


def download_xtts_model(target_dir: Path) -> None:
    snapshot_download(
        repo_id="coqui/XTTS-v2",
        local_dir=str(target_dir),
        local_dir_use_symlinks=False,
    )


def ensure_ffmpeg() -> None:
    imageio_ffmpeg.get_ffmpeg_exe()


def main() -> None:
    config = load_config()
    config.memo_model_dir.mkdir(parents=True, exist_ok=True)
    config.memo_misc_model_dir.mkdir(parents=True, exist_ok=True)
    config.xtts_model_dir.mkdir(parents=True, exist_ok=True)

    ensure_ffmpeg()
    download_memo_models(config.memo_model_dir, config.memo_misc_model_dir)
    download_xtts_model(config.xtts_model_dir)


if __name__ == "__main__":
    main()
