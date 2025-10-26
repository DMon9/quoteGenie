FROM python:3.11-slim
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy orchestrator code
COPY . .

# Run uvicorn directly on router.py
CMD ["uvicorn", "router:app", "--host", "0.0.0.0", "--port", "8000"]
