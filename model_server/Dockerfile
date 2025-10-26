FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server.py .

# Model will be mounted as a volume at /model
VOLUME /model

# Expose port
EXPOSE 11434

# Environment variables
ENV MODEL_PATH=/model
ENV HOST=0.0.0.0
ENV PORT=11434

# Run the server
CMD ["python", "server.py"]
