FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOME=/home/app \
    HF_HOME=/home/app/.cache/huggingface \
    TRANSFORMERS_CACHE=/home/app/.cache/huggingface

WORKDIR /app

# libgomp1 is required by the CPU-backed PyTorch/Sentence Transformers stack.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 libmagic1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# The app writes rotating logs and caches downloaded embedding data at runtime.
RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/logs /app/.cache_embeddings /home/app/.cache/huggingface \
    && chown -R appuser:appuser /app /home/app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]