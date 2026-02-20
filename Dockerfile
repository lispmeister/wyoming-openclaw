FROM python:3.11-slim

WORKDIR /app

# Install tini first for proper signal handling
RUN apt-get update && apt-get install -y --no-install-recommends tini && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY wyoming_openclaw.py .

# Expose Wyoming port
EXPOSE 10600

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "wyoming_openclaw.py"]
