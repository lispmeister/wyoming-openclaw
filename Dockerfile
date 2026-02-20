FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY wyoming_openclaw.py .

# Expose Wyoming port
EXPOSE 10600

# Use tini for proper signal handling
RUN pip install --no-cache-dir tini
ENTRYPOINT ["tini", "--"]
CMD ["python", "wyoming_openclaw.py"]
