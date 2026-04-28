FROM pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MEMO_REPO_PATH=/app/memo_upstream \
    MEMO_CONFIG_PATH=/app/configs/memo_inference.yaml \
    MEMO_PYTHON_EXECUTABLE=/usr/local/bin/python \
    MEMO_MODEL_DIR=/runpod-volume/models/memo \
    MEMO_MISC_MODEL_DIR=/runpod-volume/models/memo_misc \
    XTTS_MODEL_NAME=tts_models/multilingual/multi-dataset/xtts_v2 \
    XTTS_MODEL_DIR=/runpod-volume/models/xtts_v2 \
    UPLOAD_DIR=/tmp/uploads \
    RESULTS_DIR=/runpod-volume/outputs \
    HF_HOME=/runpod-volume/cache/huggingface \
    TRANSFORMERS_CACHE=/runpod-volume/cache/transformers \
    HUGGINGFACE_HUB_CACHE=/runpod-volume/cache/huggingface/hub

RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    git \
    libgl1 \
    libglib2.0-0 \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
COPY requirements-runpod.txt /app/requirements-runpod.txt
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r /app/requirements.txt && \
    pip install -r /app/requirements-runpod.txt

COPY . /app

RUN pip install -e /app/memo_upstream --no-deps && \
    mkdir -p /tmp/uploads /runpod-volume/outputs

CMD ["python", "handler.py"]
