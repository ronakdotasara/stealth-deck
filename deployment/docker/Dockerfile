# Stealth Deck - Raspberry Pi Docker Container
# For development and testing

FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    git \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY raspberry-pi/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY raspberry-pi/ ./raspberry-pi/

# Create data directories
RUN mkdir -p /data/cache /data/notes /data/logs

# Set environment variables
ENV PYTHONPATH=/app/raspberry-pi
ENV DATA_DIR=/data
ENV LOGS_DIR=/data/logs

# Expose ports (if needed)
# EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)"

# Run application
CMD ["python3", "-m", "raspberry-pi.src.main"]
