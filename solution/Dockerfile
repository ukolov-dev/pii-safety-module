FROM python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 AS runtime

ARG UV_VERSION=0.11.30

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN pip install --no-cache-dir "uv==${UV_VERSION}"

COPY pyproject.toml uv.lock ./
RUN uv export \
      --frozen \
      --no-dev \
      --no-emit-project \
      --format requirements.txt \
      --output-file /tmp/requirements.lock \
    && uv pip install --system --require-hashes -r /tmp/requirements.lock \
    && rm /tmp/requirements.lock

COPY app ./app
RUN uv pip install --system --no-deps .

RUN useradd --system --uid 10001 appuser \
    && mkdir -p /run/pii-secrets \
    && chown appuser /run/pii-secrets \
    && chmod 0700 /run/pii-secrets
USER appuser

EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health/ready', timeout=2)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
