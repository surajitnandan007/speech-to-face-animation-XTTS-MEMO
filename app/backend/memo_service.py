from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import yaml

from .config import AppConfig
from .exceptions import ConfigurationError, GenerationError
from .models import GenerationOptions


ALLOWED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
MEMO_REMOTE_MODEL = "memoavatar/memo"
REQUIRED_MEMO_MODEL_SUBDIRS = ("reference_net", "diffusion_net", "image_proj", "audio_proj")


class MemoService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.config.upload_dir.mkdir(parents=True, exist_ok=True)
        self.config.results_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        *,
        audio_file: Path,
        source_image: Path,
        output_dir: Path,
        options: GenerationOptions,
    ) -> Path:
        self._validate_runtime()

        job_dir = output_dir.resolve()
        job_dir.mkdir(parents=True, exist_ok=True)

        audio_path = self._prepare_audio_file(audio_file, job_dir / "input.wav")
        image_path = self._prepare_source_image(source_image, job_dir)
        runtime_config_path = self._materialize_runtime_config(job_dir / "memo_inference.runtime.yaml")
        command = self._build_command(audio_path, image_path, job_dir, runtime_config_path, options)

        completed = subprocess.run(
            command,
            cwd=str(self.config.memo_repo_path),
            capture_output=True,
            text=True,
            check=False,
        )
        logs = self._combine_logs(completed.stdout, completed.stderr)
        if completed.returncode != 0:
            raise GenerationError(
                "MEMO finished with an error. Check the logs below for details.",
                logs=logs,
            )

        output_video = self._find_output_video(job_dir)
        if output_video is None:
            raise GenerationError(
                "MEMO completed, but no output video was found in the results folder.",
                logs=logs,
            )

        return output_video

    def _validate_runtime(self) -> None:
        repo_path = self.config.memo_repo_path
        inference_script = repo_path / "inference.py"
        if not repo_path.exists():
            raise ConfigurationError(f"MEMO_REPO_PATH does not exist: {repo_path}")
        if not inference_script.exists():
            raise ConfigurationError(f"MEMO inference script was not found at {inference_script}.")
        if not Path(self.config.memo_python_executable).exists():
            raise ConfigurationError(
                f"MEMO_PYTHON_EXECUTABLE does not exist: {self.config.memo_python_executable}"
            )
        if not self.config.memo_config_path.exists():
            raise ConfigurationError(f"MEMO_CONFIG_PATH does not exist: {self.config.memo_config_path}")

    def _prepare_audio_file(self, source_path: Path, target_path: Path) -> Path:
        if not source_path.exists():
            raise ValueError(f"Audio file does not exist: {source_path}")
        if source_path.suffix.lower() != ".wav":
            raise ValueError("MEMO expects a .wav audio input.")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
        return target_path

    def _prepare_source_image(self, source_path: Path, output_dir: Path) -> Path:
        if source_path.suffix.lower() not in ALLOWED_IMAGE_SUFFIXES:
            supported = ", ".join(sorted(ALLOWED_IMAGE_SUFFIXES))
            raise ValueError(f"Supported source image types are: {supported}")
        destination = output_dir / f"source{source_path.suffix.lower()}"
        shutil.copy2(source_path, destination)
        return destination

    def _build_command(
        self,
        audio_path: Path,
        image_path: Path,
        output_dir: Path,
        runtime_config_path: Path,
        options: GenerationOptions,
    ) -> list[str]:
        inference_script = self.config.memo_repo_path / "inference.py"
        return [
            self.config.memo_python_executable,
            str(inference_script),
            "--config",
            str(runtime_config_path),
            "--input_image",
            str(image_path),
            "--input_audio",
            str(audio_path),
            "--output_dir",
            str(output_dir),
            "--seed",
            str(options.seed),
        ]

    def _materialize_runtime_config(self, target_path: Path) -> Path:
        config_data = yaml.safe_load(self.config.memo_config_path.read_text(encoding="utf-8"))
        config_data["model_name_or_path"] = self._resolve_model_name_or_path()
        config_data["misc_model_dir"] = str(self.config.memo_misc_model_dir)
        target_path.write_text(yaml.safe_dump(config_data, sort_keys=False), encoding="utf-8")
        return target_path

    def _resolve_model_name_or_path(self) -> str:
        if all((self.config.memo_model_dir / subdir).exists() for subdir in REQUIRED_MEMO_MODEL_SUBDIRS):
            return str(self.config.memo_model_dir)
        return MEMO_REMOTE_MODEL

    @staticmethod
    def _combine_logs(stdout: str, stderr: str) -> str:
        parts = [part.strip() for part in (stdout, stderr) if part.strip()]
        return "\n\n".join(parts)

    @staticmethod
    def _find_output_video(result_dir: Path) -> Path | None:
        candidates = sorted(
            result_dir.rglob("*.mp4"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        return candidates[0] if candidates else None
