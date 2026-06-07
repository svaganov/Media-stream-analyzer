FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3.11 python3.11-pip python3.11-venv \
    ffmpeg \
    libsrt-dev \
    libndi-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt requirements-dev.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy source
COPY src/ ./src/
COPY docs/ ./docs/
COPY scripts/ ./scripts/
COPY examples/ ./examples/

# Expose ports
EXPOSE 8000

# Entrypoint
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
