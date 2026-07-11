# syntax=docker/dockerfile:1.7

FROM ghcr.io/ggml-org/llama.cpp:light

ARG QWEN_MODE=thinking

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    QWEN_ENABLED=1 \
    QWEN_BINARY=/app/llama-completion \
    QWEN_MODEL_PATH=/app/models/Qwen3-4B-Q4_K_M.gguf \
    QWEN_THREADS=2 \
    QWEN_CONTEXT_SIZE=4096 \
    QWEN_MAX_TOKENS=2048 \
    QWEN_TIMEOUT_SECONDS=360 \
    QWEN_MODE=${QWEN_MODE} \
    QWEN_SEED=42

WORKDIR /app

RUN mkdir -p /app/models && python3 - <<'PY'
import urllib.request
from pathlib import Path

url = (
    "https://huggingface.co/"
    "Qwen/Qwen3-4B-GGUF/resolve/main/"
    "Qwen3-4B-Q4_K_M.gguf?download=true"
)
destination = Path("/app/models/Qwen3-4B-Q4_K_M.gguf")
request = urllib.request.Request(url, headers={"User-Agent": "RouteIQ-v1.4"})
downloaded = 0
with urllib.request.urlopen(request, timeout=180) as response, destination.open("wb") as output:
    while True:
        chunk = response.read(8 * 1024 * 1024)
        if not chunk:
            break
        output.write(chunk)
        downloaded += len(chunk)
        if downloaded % (200 * 1024 * 1024) < len(chunk):
            print(f"Downloaded {downloaded // (1024 * 1024)} MB", flush=True)
if destination.stat().st_size < 2_000_000_000:
    raise RuntimeError("Qwen 4B model download is incomplete")
print(f"Qwen 4B model ready: {destination.stat().st_size / 1_000_000_000:.2f} GB", flush=True)
PY

COPY agent.py /app/agent.py
COPY local /app/local

ENTRYPOINT ["python3", "/app/agent.py"]
