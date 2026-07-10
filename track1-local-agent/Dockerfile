FROM debian:bookworm-slim AS llama-builder

ARG LLAMA_CPP_TAG=b9950

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       ca-certificates \
       cmake \
       git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone \
      --depth 1 \
      --branch "${LLAMA_CPP_TAG}" \
      https://github.com/ggml-org/llama.cpp.git \
      /src/llama.cpp

RUN cmake \
      -S /src/llama.cpp \
      -B /src/llama.cpp/build \
      -DGGML_NATIVE=OFF \
      -DGGML_OPENMP=ON \
      -DLLAMA_CURL=OFF \
      -DBUILD_SHARED_LIBS=OFF \
      -DCMAKE_BUILD_TYPE=Release \
    && cmake \
      --build /src/llama.cpp/build \
      --target llama-cli \
      --parallel 2


FROM debian:bookworm-slim AS model-downloader

ARG GEMMA_MODEL_URL="https://huggingface.co/ggml-org/gemma-3-1b-it-GGUF/resolve/main/gemma-3-1b-it-Q4_K_M.gguf?download=true"
ARG GEMMA_MODEL_SHA256="8ccc5cd1f1b3602548715ae25a66ed73fd5dc68a210412eea643eb20eb75a135"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
       curl \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /models /licenses \
    && curl \
       --fail \
       --location \
       --retry 5 \
       --retry-delay 3 \
       "${GEMMA_MODEL_URL}" \
       --output /models/gemma-3-1b-it-Q4_K_M.gguf \
    && echo \
       "${GEMMA_MODEL_SHA256}  /models/gemma-3-1b-it-Q4_K_M.gguf" \
       | sha256sum --check - \
    && curl \
       --fail \
       --location \
       --retry 5 \
       https://ai.google.dev/gemma/terms \
       --output /licenses/GEMMA_TERMS_OF_USE.html


FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
       libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=llama-builder \
  /src/llama.cpp/build/bin/llama-cli \
  /usr/local/bin/llama-cli

COPY --from=model-downloader \
  /models/gemma-3-1b-it-Q4_K_M.gguf \
  /models/gemma-3-1b-it-Q4_K_M.gguf

COPY --from=model-downloader \
  /licenses/GEMMA_TERMS_OF_USE.html \
  /licenses/GEMMA_TERMS_OF_USE.html

COPY GEMMA_NOTICE.txt /licenses/GEMMA_NOTICE.txt
COPY agent.py /app/agent.py

ENV ROUTEIQ_LOCAL_GEMMA_MODEL="/models/gemma-3-1b-it-Q4_K_M.gguf"
ENV ROUTEIQ_LOCAL_GEMMA_THREADS="2"
ENV ROUTEIQ_LOCAL_GEMMA_CONTEXT="1024"

ENTRYPOINT ["python3", "/app/agent.py"]
