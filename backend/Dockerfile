# syntax=docker/dockerfile:1
FROM python:3.12-slim
# This is heavily inspired by https://github.com/fastapi/full-stack-fastapi-template

# Add PGDG apt repo for PostgreSQL 18 client tools
RUN apt-get update && apt-get install -y --no-install-recommends wget gnupg ca-certificates && \
    wget --quiet -O /usr/share/keyrings/postgresql-archive-keyring.gpg \
        https://www.postgresql.org/media/keys/ACCC4CF8.asc && \
    echo "deb [signed-by=/usr/share/keyrings/postgresql-archive-keyring.gpg] https://apt.postgresql.org/pub/repos/apt/ $(. /etc/os-release && echo $VERSION_CODENAME)-pgdg main" \
        > /etc/apt/sources.list.d/pgdg.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends postgresql-client-18 && \
    rm -rf /var/lib/apt/lists/*



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
COPY ./app /app/app
# COPY ./tests/ /app/tests

# Sync with project installed
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync 

# Default command for production
CMD ["fastapi", "run", "--workers", "4", "app/main.py"]
