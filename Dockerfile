# Multi-Agent Competition System - Hugging Face Spaces Dockerfile
# Uses uv for fast, reliable Python package management

# Stage 1: Build dependencies
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

# Set working directory
WORKDIR /app

# Enable bytecode compilation for faster startup
ENV UV_COMPILE_BYTECODE=1

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (production only, no dev dependencies)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Stage 2: Runtime image
FROM python:3.13-slim-bookworm

# Set working directory
WORKDIR /app

# Copy Python environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application source
COPY src/ ./src/
COPY config.toml ./
COPY .env.example ./

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    # Create temp directory for DuckDB
    mkdir -p /tmp && \
    chmod 777 /tmp

# Switch to non-root user
USER appuser

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    # Hugging Face Spaces defaults
    PORT=7860 \
    HOST=0.0.0.0 \
    # DuckDB location (ephemeral)
    DUCKDB_PATH=/tmp/agent_leaderboard.duckdb

# Expose port (Hugging Face Spaces default)
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860')"

# Run application
CMD ["python", "src/main.py", "--host", "0.0.0.0", "--port", "7860"]
