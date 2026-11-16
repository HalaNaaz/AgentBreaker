# Multi-stage Docker build for AgentBreaker AI Red Teaming Framework
# Stage 1: Build wheel
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE NOTICE ./
COPY src/ ./src/
COPY payloads/ ./payloads/

RUN pip install --no-cache-dir hatchling
RUN python -m pip install --no-cache-dir build && python -m build --wheel

# Stage 2: Final minimal runtime image
FROM python:3.12-slim AS runtime

# Security: metadata labels
LABEL org.opencontainers.image.title="AgentBreaker" \
      org.opencontainers.image.description="Modular AI Red Teaming & Security Testing Framework" \
      org.opencontainers.image.vendor="AshlynxCyber Security Systems" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.version="0.1.0"

# Install runtime OS dependencies for secure storage & health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    dbus-x11 \
    gnome-keyring \
    libsecret-1-0 \
    && rm -rf /var/lib/apt/lists/*

# Security: Non-root user (least privilege)
RUN groupadd -g 10001 agentbreaker && \
    useradd -u 10001 -g agentbreaker -s /bin/bash -m agentbreaker

WORKDIR /app

# Copy wheel from builder and install
COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm -rf /tmp/*.whl

# Create data directory and assign ownership
RUN mkdir -p /home/agentbreaker/.agentbreaker && \
    chown -R agentbreaker:agentbreaker /home/agentbreaker

# Switch to non-root user
USER agentbreaker
ENV AGENTBREAKER_HOME=/home/agentbreaker/.agentbreaker \
    PYTHONUNBUFFERED=1

# Expose API port (bound to loopback in compose)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD agentbreaker info || exit 1

ENTRYPOINT ["agentbreaker"]
CMD ["info"]
