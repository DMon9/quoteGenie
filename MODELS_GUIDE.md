# QuoteGenie Models Guide

Complete guide for managing LLM models with **SD card storage support** and Docker deployment.

---

## Overview

QuoteGenie supports multiple model backends:

1. **Ollama** – For orchestrator LangChain chains (default: `llama3.2:1b` on port `11435`)
2. **HuggingFace model_server** – Self-hosted models from HF Hub (ports `11400`–`11407`)
3. **Backend vision** – Optional Ollama or other LLM for vision tasks (port `11434`)

All HuggingFace models are **stored locally** and mounted into Docker containers—no Docker registry downloads needed.

---

## SD Card Storage Setup

### 1. Quick Setup (Windows)

```powershell
# Auto-configure SD card storage (D:\quoteGenie_models)
.\setup_sdcard.ps1
```

Or manually:

```powershell
# Set environment variable for this session
$env:MODELS_DIR="D:\quoteGenie_models"

# Add to .env file
Add-Content -Path .env -Value "`nMODELS_DIR=D:\quoteGenie_models"

# Create directory
New-Item -ItemType Directory -Path D:\quoteGenie_models -Force
```

### 2. Verify Storage

```powershell
# Check available space
Get-Volume -DriveLetter D
```

**Recommended:** At least 20 GB free for 1–2 medium models.

---

## Available Models

| Model | Size | Description | Auth Required | Port |
|-------|------|-------------|--------------|------|
| **tinyllama** | ~2 GB | TinyLlama 1.1B Chat – fast, tiny, ideal for SD cards | No | 11406 |
| **qwen25_0_5b** | ~1 GB | Qwen2.5 0.5B Instruct – ultra-compact | No | 11407 |
| **mistral** | ~14 GB | Mistral 7B Instruct v0.2 | No | 11401 |
| **qwen2** | ~15 GB | Qwen2 7B Instruct | No | 11402 |
| **moondream2** | ~4 GB | Vision-language model for image analysis | No | 11403 |
| **gemma2** | ~18 GB | Google Gemma 2 9B Instruct | Yes (EULA) | 11404 |
| **llama3** | ~16 GB | Meta Llama 3 8B Instruct | Yes | 11400 |
| **llama31** | ~16 GB | Meta Llama 3.1 8B Instruct | Yes | 11405 |
| **deepseek** | ~13 GB | DeepSeek Coder 6.7B Instruct | No | — |
| **granite** | ~16 GB | IBM Granite 3.0 8B Instruct | No | — |
| **phi4** | ~28 GB | Microsoft Phi-4 | No | — |

> **Pro Tip:** Start with `tinyllama` or `qwen25_0_5b` for quick testing on limited storage.

---

## Download Models

### List Available Models

```powershell
D:/sd/Scripts/python.exe download_models.py --list
```

### Download Single Model

```powershell
# Download to default location (./models) or SD card if MODELS_DIR is set
D:/sd/Scripts/python.exe download_models.py --model tinyllama
```

### Download Multiple Models

```powershell
D:/sd/Scripts/python.exe download_models.py --model tinyllama --model qwen25_0_5b
```

### Download All Models

```powershell
# WARNING: Requires ~100+ GB storage
D:/sd/Scripts/python.exe download_models.py --all
```

### For Gated Models (Llama 3, Gemma 2)

1. Get your HuggingFace token: https://huggingface.co/settings/tokens
2. Accept the model's EULA on HuggingFace
3. Set environment variable:

```powershell
$env:HF_TOKEN="hf_your_token_here"
D:/sd/Scripts/python.exe download_models.py --model llama31
```

---

## Running Models

### Start Model with Docker Compose

```powershell
# Start a single model
docker-compose --profile models up tinyllama

# Start multiple models
docker-compose --profile models up tinyllama qwen25_0_5b

# Start orchestrator + model
docker-compose up orchestrator
docker-compose --profile models up tinyllama
```

### Verify Model Health

```powershell
# Quick health check for all model endpoints
D:/sd/Scripts/python.exe scripts/healthcheck_models.py
```

Expected output:

```
[PASS] model_server:11406/health (status=200, time=42ms) | type=text, device=cpu
[PASS] model_server:11407/health (status=200, time=38ms) | type=text, device=cpu
[FAIL] ollama:11435/tags (status=-, time=-) | All connection attempts failed
```

> Models not running will show `[FAIL]`. This is normal if you haven't started them yet.

---

## Configuration

### Environment Variables

Add to `.env` file:

```bash
# Model storage location (default: ./models)
MODELS_DIR=D:\quoteGenie_models

# Ollama settings (for orchestrator chains)
OLLAMA_BASE_URL=http://localhost:11435
OLLAMA_MODEL=llama3.2:1b

# HuggingFace token (for gated models)
HF_TOKEN=hf_your_token_here
```

### Docker Compose Profiles

Models use the `models` profile to avoid auto-starting:

```yaml
profiles: ["models"]
```

Start specific models:

```powershell
# Start only tinyllama
docker-compose --profile models up tinyllama

# Start all model servers (uses ~40+ GB RAM)
docker-compose --profile models up
```

---

## Usage Examples

### 1. Test Generation (Direct HTTP)

```powershell
# Test tinyllama model
$body = @{
    prompt = "Write a haiku about construction"
    max_tokens = 50
    temperature = 0.7
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:11406/api/generate" `
                  -Method Post `
                  -ContentType "application/json" `
                  -Body $body
```

### 2. Vision Analysis (moondream2)

```powershell
# Encode image to base64
$bytes = [System.IO.File]::ReadAllBytes("path\to\image.jpg")
$base64 = [Convert]::ToBase64String($bytes)

$body = @{
    image = $base64
    prompt = "Describe this construction site"
    max_tokens = 200
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:11403/api/vision" `
                  -Method Post `
                  -ContentType "application/json" `
                  -Body $body
```

### 3. Orchestrator Integration

The `orchestrator` service uses **Ollama** by default. To use a HuggingFace model instead:

1. Update `orchestrator/ai_chain.py`:

```python
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://tinyllama:11434")
```

2. Change the LLM wrapper:

```python
from langchain_community.llms import HuggingFaceTextGenInference
llm = HuggingFaceTextGenInference(
    inference_server_url="http://tinyllama:11434",
    max_new_tokens=512
)
```

---

## Troubleshooting

### Model Won't Start

**Check Docker logs:**

```powershell
docker logs tinyllama
```

**Common issues:**

- **Model directory empty:** Download the model first with `download_models.py`
- **Out of memory:** Reduce memory limit in `docker-compose.yml` or use a smaller model
- **Port conflict:** Another service is using the port—change the port mapping

### Model Responds Slowly

- **CPU mode:** Model servers use CPU by default. For GPU, ensure Docker has GPU support.
- **Model too large:** Try a smaller model like `tinyllama` or `qwen25_0_5b`.

### Health Check Fails

```powershell
# Verify the container is running
docker ps

# Check specific port
curl http://localhost:11406/health

# Restart container
docker-compose restart tinyllama
```

---

## Best Practices

### For SD Card Storage

1. **Start small:** Use `tinyllama` (2 GB) or `qwen25_0_5b` (1 GB) first.
2. **Check space:** Monitor free space with `Get-Volume -DriveLetter D`.
3. **One at a time:** Download and test one model before downloading more.

### For Production

1. **GPU acceleration:** Use `nvidia-docker` and update `docker-compose.yml`:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

2. **Model caching:** Download models once, reuse across containers with `MODELS_DIR`.
3. **Health monitoring:** Use `healthcheck_models.py` in CI/CD pipelines.

---

## Advanced: Custom Models

### Add a New Model

1. **Update `download_models.py`:**

```python
MODEL_CONFIGS = {
    # ... existing ...
    "custom_model": {
        "repo_id": "org/model-name",
        "requires_auth": False,
        "description": "My custom model"
    }
}
```

2. **Download the model:**

```powershell
D:/sd/Scripts/python.exe download_models.py --model custom_model
```

3. **Add to `docker-compose.yml`:**

```yaml
custom_model:
  build: ./model_server
  container_name: custom_model
  ports:
    - "11408:11434"
  volumes:
    - ${MODELS_DIR:-./models}/custom_model:/model:ro
  environment:
    - MODEL_PATH=/model
    - MODEL_TYPE=text
    - PORT=11434
  profiles: ["models"]
```

4. **Start the model:**

```powershell
docker-compose --profile models up custom_model
```

---

## Summary

| Task | Command |
|------|---------|
| Setup SD card | `.\setup_sdcard.ps1` |
| List models | `D:/sd/Scripts/python.exe download_models.py --list` |
| Download model | `D:/sd/Scripts/python.exe download_models.py --model tinyllama` |
| Start model | `docker-compose --profile models up tinyllama` |
| Health check | `D:/sd/Scripts/python.exe scripts/healthcheck_models.py` |
| View logs | `docker logs tinyllama` |

**Next Steps:**

1. ✅ SD card configured at `D:\quoteGenie_models`
2. ✅ Downloaded `tinyllama` and `qwen25_0_5b`
3. ▶️ Test models: `docker-compose --profile models up tinyllama`
4. 🔍 Verify: `D:/sd/Scripts/python.exe scripts/healthcheck_models.py`

---

For orchestrator LangChain integration, see `orchestrator/ai_chain.py` and `orchestrator/phase_chain.py`.
