param(
    [switch]$SkipModelDownload
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$VenvPath = Join-Path $RepoRoot ".venv"
$PythonExe = Join-Path $VenvPath "Scripts\\python.exe"
$PipExe = Join-Path $VenvPath "Scripts\\pip.exe"
$MemoPackages = @(
    "accelerate==1.1.1",
    "albumentations==1.4.21",
    "diffusers==0.31.0",
    "einops==0.8.0",
    "ffmpeg-python==0.2.0",
    "funasr==1.0.27",
    "huggingface-hub==0.26.2",
    "hydra-core==1.3.2",
    "imageio==2.36.0",
    "librosa==0.10.2.post1",
    "mediapipe==0.10.18",
    "modelscope==1.20.1",
    "moviepy==1.0.3",
    "numpy==1.26.4",
    "omegaconf==2.3.0",
    "onnxruntime==1.20.1",
    "opencv-python-headless==4.10.0.84",
    "pillow==10.4.0",
    "scikit-learn==1.5.2",
    "scipy==1.14.1",
    "transformers==4.46.3",
    "tqdm==4.67.1"
)

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python launcher 'py' was not found. Install Python 3.11 first."
}

if (-not (Test-Path $PythonExe)) {
    py -3.11 -m venv $VenvPath
}

& $PythonExe -m pip install --upgrade pip setuptools wheel
& $PipExe install -r (Join-Path $RepoRoot "requirements.txt")
& $PipExe install torch==2.5.1 torchaudio==2.5.1 torchvision==0.20.1
& $PipExe install @MemoPackages
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
& $PipExe install -e (Join-Path $RepoRoot "memo_upstream") --no-deps
if ($LASTEXITCODE -ne 0) { throw "Editable MEMO install failed." }

if (-not $SkipModelDownload) {
    & $PythonExe (Join-Path $RepoRoot "scripts\\download_models.py")
    if ($LASTEXITCODE -ne 0) { throw "Model download failed." }
}

Write-Host "Environment ready."
