# EstimateGenie Backend API

AI-powered construction estimation backend built with FastAPI, computer vision, and LLMs.

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```powershell
# Navigate to backend directory
cd backend

# Build and start services
docker-compose up --build
```

The API will be available at: http://localhost:8000

### Option 2: Local Development

```powershell
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
copy .env.example .env

# Start the API
python app.py
```

## 📋 Prerequisites

- Python 3.11+
- Docker & Docker Compose (for containerized deployment)
- Ollama (for LLM features) - optional but recommended

### Install Ollama (Optional)

```powershell
# Download and install from: https://ollama.com/download

# Pull the Llama 3 model
ollama pull llama3
```

## 🧪 Testing the API

### Health Check

```powershell
curl http://localhost:8000/health
```

### Create a Quote

```powershell
curl -X POST "http://localhost:8000/v1/quotes" \
  -F "file=@path/to/image.jpg" \
  -F "project_type=bathroom"
```

### List Quotes

```powershell
curl http://localhost:8000/v1/quotes
```

### Get Specific Quote

```powershell
curl http://localhost:8000/v1/quotes/quote_abc123
```

## 📚 API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🏗️ Project Structure

```
backend/
├── app.py                      # Main FastAPI application
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container image definition
├── docker-compose.yml          # Multi-container setup
├── .env.example               # Environment variables template
├── services/
│   ├── vision_service.py      # Computer vision pipeline
│   ├── llm_service.py         # LLM reasoning
│   └── estimation_service.py  # Cost calculation
├── database/
│   └── db.py                  # SQLite database operations
├── models/
│   └── quote.py               # Pydantic data models
└── uploads/                    # Uploaded images storage
```

## 🔧 Configuration

Edit `.env` file to configure:

- `OLLAMA_URL`: Ollama API endpoint (default: http://localhost:11434)
- `OLLAMA_MODEL`: LLM model to use (default: llama3)
- `DATABASE_PATH`: SQLite database file path
- `UPLOAD_DIR`: Directory for uploaded images

## 🤖 AI Models

### Vision Models (Optional - will use fallbacks if not available)

- **YOLOv8**: Object detection (auto-downloads on first run)
- **Depth Estimation**: Basic depth/scale estimation (placeholder)

### Language Models

- **Llama 3**: Reasoning and structured output generation (via Ollama)
- Falls back to template-based responses if Ollama unavailable

## 📊 Database

Uses SQLite for simplicity. Database schema:

### Quotes Table
- id (TEXT): Unique quote identifier
- project_type (TEXT): Type of project
- image_path (TEXT): Path to uploaded image
- vision_results (JSON): Computer vision analysis
- reasoning (JSON): LLM reasoning output
- estimate (JSON): Cost estimate breakdown
- status (TEXT): Quote status
- created_at (DATETIME): Creation timestamp
- updated_at (DATETIME): Last update timestamp

## 🛠️ Development

### Add New Material

Edit `services/estimation_service.py`:

```python
self.materials_db = {
    "new_material": {
        "price": 25.00,
        "unit": "unit",
        "description": "Material description"
    }
}
```

### Add New Labor Rate

Edit `services/estimation_service.py`:

```python
self.labor_rates = {
    "new_trade": {
        "rate": 65.00,
        "unit": "hour"
    }
}
```

## 🐛 Troubleshooting

### Port Already in Use

```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /PID <PID> /F
```

### Ollama Connection Error

- Check Ollama is running: `ollama list`
- Verify OLLAMA_URL in `.env`
- Try fallback mode (API will work without Ollama)

### Module Import Errors

```powershell
# Ensure you're in the backend directory
cd backend

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

## 🚀 Deployment

### Production Deployment

1. Set `DEBUG=false` in `.env`
2. Use a production ASGI server (Gunicorn + Uvicorn)
3. Add HTTPS via reverse proxy (Nginx, Caddy, or Cloudflare Tunnel)
4. Consider PostgreSQL instead of SQLite for scale
5. Add authentication/API keys

### Cloudflare Tunnel (Recommended)

```powershell
# Install cloudflared
# https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/

# Create tunnel
cloudflared tunnel create estimategenie-api

# Route traffic
cloudflared tunnel route dns estimategenie-api api.estimategenie.net

# Run tunnel
cloudflared tunnel run estimategenie-api --url http://localhost:8000
```

## 📝 Next Steps

1. **Fine-tune vision models** on your specific use cases
2. **Expand materials database** with real pricing data
3. **Add authentication** for production use
4. **Integrate payment processing** for premium features
5. **Add webhooks** for frontend notifications
6. **Implement caching** for frequently requested data

## 🤝 Integration with Frontend

Frontend calls should hit:
```
POST https://api.estimategenie.net/v1/quotes
```

See main project README for complete setup.

## 📄 License

© 2025 EstimateGenie, Inc. All rights reserved.
