# syntax=docker/dockerfile:1
# Reminder: This is almost directly taken from https://github.com/fastapi/full-stack-fastapi-template
# with minor changes and updates

FROM python:3.12-slim

# See: https://docs.astral.sh/uv/guides/integration/docker/#using-the-environment
# See: https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
# See: https://docs.astral.sh/uv/guides/integration/docker/#caching
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH" \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app/

# Install uv https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:0.8.22 /uv /uvx /bin/

# Install Python dependencies (only deps here)
# See: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
COPY pyproject.toml uv.lock /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# Copy over app code
COPY ./alembic.ini /app/
COPY ./app /app/app
# COPY ./tests/ /app/tests

# Sync with project installed
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync 

# Default command for production
CMD ["fastapi", "run", "--workers", "4", "app/main.py"]
