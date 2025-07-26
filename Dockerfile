FROM python:3.11-slim

LABEL org.opencontainers.image.title="glabmetrics"
LABEL org.opencontainers.image.description="CLI tool for GitLab instance analysis and HTML report generation"
LABEL org.opencontainers.image.vendor="CDDS AB"
LABEL org.opencontainers.image.source="https://github.com/cdds-ab/glabmetrics"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PDM_CHECK_UPDATE=false

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install PDM
RUN pip install pdm

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /home/app

# Copy project files
COPY --chown=app:app pyproject.toml pdm.lock README.md LICENSE ./
COPY --chown=app:app glabmetrics/ ./glabmetrics/

# Configure PDM to use PEP582 instead of venv
ENV PDM_USE_VENV=false

# Install dependencies
RUN pdm install --prod --no-editable

# Create directories for output
RUN mkdir -p /home/app/output /home/app/data

# Set the PATH to include PEP582 bin directory
ENV PATH="/home/app/__pypackages__/3.11/bin:$PATH"

# Default command - use PDM run for proper environment
ENTRYPOINT ["pdm", "run", "glabmetrics"]
CMD ["--help"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import glabmetrics; print('OK')" || exit 1

# Volumes for data persistence
VOLUME ["/home/app/output", "/home/app/data"]