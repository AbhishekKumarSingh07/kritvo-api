# Kritvo backend image (API by default; the gateway and worker override the command).
# Build: docker build -t kritvo-api .
FROM python:3.13-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Dependencies first, for better layer caching.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY README.md ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

FROM python:3.13-slim AS runtime
RUN useradd --create-home --uid 10001 app
WORKDIR /app
COPY --from=build --chown=app:app /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production
USER app
EXPOSE 8000
CMD ["uvicorn", "kritvo.main_api:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
