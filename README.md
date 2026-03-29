# XTTS + MEMO Media Pipeline

This workspace implements a text-or-audio to talking-face pipeline inspired by the orchestration style in `surajitnandan007/speech-to-face-animation-with-piper-sadtalker`, but swaps the generation stack to:

- XTTS v2 for text-to-speech
- MEMO for audio-driven face animation

## What is included

- A local CLI pipeline that accepts either `--text` or `--audio-path`
- XTTS voice cloning from `--speaker-wav`
- MEMO inference wrapper for a single source image and speech audio
- A setup script that creates a Python 3.11 virtual environment, installs dependencies, and downloads weights
- An optional XTTS runtime install script for machines with Visual C++ build tools
- Windows-friendly MEMO patches for model downloads and ffmpeg resolution

## Quick start

1. Create and install the environment:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap.ps1
```

2. If you want XTTS text generation on Windows, install the runtime after adding Microsoft C++ Build Tools:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_xtts_runtime.ps1
```

3. Optionally copy `.env.example` to `.env` and set defaults.

4. Run the pipeline:

```powershell
.\.venv\Scripts\python.exe .\run_pipeline.py `
  --text "Hello from XTTS and MEMO." `
  --speaker-wav C:\path\to\speaker.wav `
  --source-image C:\path\to\face.jpg `
  --output-dir .\outputs\demo
```

Or reuse existing audio:

```powershell
.\.venv\Scripts\python.exe .\run_pipeline.py `
  --audio-path C:\path\to\speech.wav `
  --source-image C:\path\to\face.jpg `
  --output-dir .\outputs\demo_audio
```

## Notes

- MEMO upstream recommends a CUDA GPU. The wrapper still installs on Windows, but real inference speed and memory use depend heavily on your hardware.
- `scripts/bootstrap.ps1` downloads the MEMO and XTTS weights, but XTTS text synthesis itself still depends on the `TTS` runtime package. On this Windows machine that package requires Microsoft Visual C++ build tools.
- The setup script defaults to CPU-safe packages where possible on this machine. If you later move to a CUDA box, adjust the install commands in [scripts/bootstrap.ps1](/workspace/scripts/bootstrap.ps1).
