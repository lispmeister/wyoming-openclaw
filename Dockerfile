FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY wyoming_clawdbot.py .

# Expose Wyoming port
EXPOSE 10600

# Run the server
ENTRYPOINT ["python", "wyoming_clawdbot.py"]
CMD ["--host", "0.0.0.0", "--port", "10600"]
