# syntax=docker/dockerfile:1.7

ARG PYTHON_VERSION=3.12

FROM ghcr.io/astral-sh/uv:0.5-python${PYTHON_VERSION}-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

COPY pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project --no-dev

COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev


FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    DALGO_TRANSPORT=streamable-http \
    DALGO_HOST=0.0.0.0 \
    DALGO_PORT=8079

RUN groupadd --system --gid 1001 dalgo \
    && useradd --system --uid 1001 --gid dalgo --home /app --shell /usr/sbin/nologin dalgo

WORKDIR /app

COPY --from=builder --chown=dalgo:dalgo /app/.venv /app/.venv
COPY --chown=dalgo:dalgo src ./src
COPY --chown=dalgo:dalgo pyproject.toml ./

USER dalgo

EXPOSE 8079

ENTRYPOINT ["dalgo-mcp"]
