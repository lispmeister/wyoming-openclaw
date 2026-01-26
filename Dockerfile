FROM python:3.11-slim

WORKDIR /app

# Install Node.js and git
RUN apt-get update && apt-get install -y curl git && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install clawdbot
RUN npm install -g clawdbot

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY wyoming_clawdbot.py .

# Expose Wyoming port
EXPOSE 10600

ENTRYPOINT ["python", "wyoming_clawdbot.py"]
CMD ["--host", "0.0.0.0", "--port", "10600"]
