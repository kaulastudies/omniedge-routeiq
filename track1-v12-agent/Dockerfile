# syntax=docker/dockerfile:1.7

FROM ghcr.io/ggml-org/llama.cpp:light

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    QWEN_ENABLED=1 \
    QWEN_BINARY=/app/llama-completion \
    QWEN_MODEL_PATH=/app/models/Qwen3-1.7B-Q8_0.gguf \
    QWEN_THREADS=2 \
    QWEN_CONTEXT_SIZE=4096 \
    QWEN_MAX_TOKENS=1024 \
    QWEN_TIMEOUT_SECONDS=240 \
    QWEN_BATCH_SIZE=4

WORKDIR /app

RUN mkdir -p /app/models && python3 - <<'PY'
import hashlib
import urllib.request
from pathlib import Path

url = (
    "https://huggingface.co/"
    "Qwen/Qwen3-1.7B-GGUF/resolve/main/"
    "Qwen3-1.7B-Q8_0.gguf?download=true"
)

destination = Path(
    "/app/models/Qwen3-1.7B-Q8_0.gguf"
)

request = urllib.request.Request(
    url,
    headers={
        "User-Agent": "RouteIQ-v1.2",
    },
)

downloaded = 0
next_report = 100 * 1024 * 1024

with urllib.request.urlopen(
    request,
    timeout=120,
) as response:
    with destination.open("wb") as output:
        while True:
            chunk = response.read(
                8 * 1024 * 1024
            )

            if not chunk:
                break

            output.write(chunk)
            downloaded += len(chunk)

            if downloaded >= next_report:
                print(
                    "Downloaded "
                    f"{downloaded // (1024 * 1024)} MB",
                    flush=True,
                )

                next_report += (
                    100 * 1024 * 1024
                )

if destination.stat().st_size < 1_000_000_000:
    raise RuntimeError(
        "Qwen model download is incomplete"
    )

print(
    "Qwen model ready: "
    f"{destination.stat().st_size / 1_000_000_000:.2f} GB",
    flush=True,
)
PY

COPY agent.py /app/agent.py
COPY local /app/local

ENTRYPOINT ["python3", "/app/agent.py"]
