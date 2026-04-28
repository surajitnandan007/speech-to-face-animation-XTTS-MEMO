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

## RunPod Serverless deployment

This repo is prepared for a queue-based RunPod Serverless endpoint:

- `handler.py` exposes the RunPod worker handler.
- `Dockerfile` builds a CUDA 12.1 PyTorch image and installs XTTS, MEMO, and serverless dependencies.
- `test_input.json` provides a container-local smoke-test payload using the sample MEMO assets.

### Deploy from GitHub

1. Push this repository to GitHub.
2. In the RunPod console, connect your GitHub account under Settings > Connections.
3. Go to Serverless > New Endpoint > Import Git Repository.
4. Select this repository, branch `main`, and Dockerfile path `Dockerfile`.
5. Choose endpoint type `Queue`.
6. Select a CUDA GPU. MEMO upstream reports testing on H100 and RTX 4090; use a high-memory GPU for practical runs.
7. Use these environment variables unless you have custom storage paths:

```text
MEMO_REPO_PATH=/app/memo_upstream
MEMO_CONFIG_PATH=/app/configs/memo_inference.yaml
MEMO_PYTHON_EXECUTABLE=/usr/local/bin/python
MEMO_MODEL_DIR=/runpod-volume/models/memo
MEMO_MISC_MODEL_DIR=/runpod-volume/models/memo_misc
XTTS_MODEL_NAME=tts_models/multilingual/multi-dataset/xtts_v2
XTTS_MODEL_DIR=/runpod-volume/models/xtts_v2
UPLOAD_DIR=/tmp/uploads
RESULTS_DIR=/runpod-volume/outputs
HF_HOME=/runpod-volume/cache/huggingface
TRANSFORMERS_CACHE=/runpod-volume/cache/transformers
HUGGINGFACE_HUB_CACHE=/runpod-volume/cache/huggingface/hub
```

The first request may be slow while Hugging Face, ModelScope, XTTS, and MEMO assets are downloaded into the RunPod volume/cache.

### API input

Use either existing audio:

```json
{
  "input": {
    "audio_url": "https://your-storage.example/speech.wav",
    "source_image_url": "https://your-storage.example/face.jpg",
    "return_video_base64": false,
    "options": {
      "seed": 42,
      "language": "en"
    }
  }
}
```

Or text-to-speech with a speaker reference:

```json
{
  "input": {
    "text": "Hello from XTTS and MEMO.",
    "speaker_wav_url": "https://your-storage.example/speaker.wav",
    "source_image_url": "https://your-storage.example/face.jpg",
    "return_video_base64": false,
    "options": {
      "seed": 42,
      "language": "en"
    }
  }
}
```

Large videos should be uploaded to object storage from the worker in production. `return_video_base64` is available for small tests, but RunPod response payload limits make it a poor fit for long videos.

### Invoke the endpoint

Set your RunPod credentials:

```powershell
$env:RUNPOD_API_KEY="your_runpod_api_key"
$env:RUNPOD_ENDPOINT_ID="your_endpoint_id"
```

Submit an async job and poll status:

```powershell
.\.venv\Scripts\python.exe .\scripts\invoke_runpod.py `
  --input-json '{"audio_url":"https://your-storage.example/speech.wav","source_image_url":"https://your-storage.example/face.jpg","return_video_base64":false}'
```

For a short synchronous smoke test:

```powershell
.\.venv\Scripts\python.exe .\scripts\invoke_runpod.py `
  --sync `
  --input-json '{"audio_path":"memo_upstream/assets/examples/speech.wav","source_image_path":"memo_upstream/assets/examples/dicaprio.jpg","return_video_base64":false}'
```
