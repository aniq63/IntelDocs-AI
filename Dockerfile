# syntax=docker/dockerfile:1

###############################################################################
# Builder stage: compile any packages that need a full toolchain, then copy
# only the resulting .so files into the slim runtime image.
###############################################################################
FROM python:3.11-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /wheels
COPY requirements.txt ./

# Install CPU-only PyTorch first (avoids the ~2GB CUDA build), then the rest.
# The torch CPU wheel is much smaller and works for CPU-backed embeddings.
RUN pip install --no-cache-dir \
        torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

###############################################################################
# Runtime stage: minimal image, no compiler toolchain.
###############################################################################
FROM python:3.11-slim AS runtime

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/home/app \
    HF_HOME=/home/app/.cache/huggingface \
    TRANSFORMERS_CACHE=/home/app/.cache/huggingface

WORKDIR /app

# libgomp1 is required by the CPU-backed PyTorch/Sentence Transformers stack.
# libmagic1 is required by the `unstructured`/python-magic loaders.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 libmagic1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
# Copy the fully-installed site-packages from the builder, preserving compiled
# binaries that needed the toolchain, then install nothing else.
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

# The app writes rotating logs and caches downloaded embedding data at runtime.
RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/logs /app/.cache_embeddings /home/app/.cache/huggingface \
    && chown -R appuser:appuser /app /home/app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
