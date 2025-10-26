# Hugging Face Models Setup (Docker Registry Bypass)

This guide shows you how to run AI models locally by mounting Hugging Face models directly into Docker containers, completely bypassing Docker Hub registry pulls.

## Overview

**Before:** Download models from Docker registry (`ollama/llama3:latest`)  
**After:** Download models from Hugging Face and mount them as volumes

## Benefits

- ✅ No dependency on Docker registry
- ✅ Full control over model versions
- ✅ Direct access to thousands of HuggingFace models
- ✅ Faster iterations (no registry pulls)
- ✅ Works offline after initial download

## Quick Start

### 1. Install Dependencies

```powershell
# Install huggingface_hub
pip install huggingface_hub
```

### 2. Download Models

```powershell
# List available models
python download_models.py --list

# Download a specific model
python download_models.py --model mistral

# Download multiple models
python download_models.py --model mistral --model qwen2

# Download all models (requires significant disk space)
python download_models.py --all
```

### 3. Set Up Authentication (Optional)

Some models like Llama 3 require Hugging Face authentication:

```powershell
# Get your token from: https://huggingface.co/settings/tokens
$env:HF_TOKEN="hf_your_token_here"

# Then download
python download_models.py --model llama3
```

### 4. Run with Docker Compose

```powershell
# Run orchestrator only
docker-compose up orchestrator

# Run with specific models
docker-compose --profile models up llama3 mistral qwen2

# Run all models (docker-compose.ai.yml)
docker-compose -f docker-compose.ai.yml up
```

## Architecture

```
┌─────────────────────────────────────────┐
│  Host Machine                           │
│  ┌───────────────────────────────────┐  │
│  │  models/                          │  │
│  │  ├── llama3/                      │  │
│  │  ├── mistral/                     │  │
│  │  ├── qwen2/                       │  │
│  │  └── moondream2/                  │  │
│  └───────────────────────────────────┘  │
│            ↓ mounted as volumes         │
│  ┌───────────────────────────────────┐  │
│  │  Docker Containers                │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │ llama3:11400                │  │  │
│  │  │ /model → ./models/llama3    │  │  │
│  │  └─────────────────────────────┘  │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │ mistral:11401               │  │  │
│  │  │ /model → ./models/mistral   │  │  │
│  │  └─────────────────────────────┘  │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## Model Server API

Each model container exposes a FastAPI server with these endpoints:

### Text Generation
```bash
curl -X POST http://localhost:11400/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing in simple terms",
    "max_tokens": 512,
    "temperature": 0.7
  }'
```

### Vision Analysis (moondream2 only)
```bash
curl -X POST http://localhost:11403/api/vision \
  -H "Content-Type: application/json" \
  -d '{
    "image": "<base64_encoded_image>",
    "prompt": "What materials do you see in this construction photo?",
    "max_tokens": 512
  }'
```

### Chat Format
```bash
curl -X POST http://localhost:11400/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is the capital of France?",
    "max_tokens": 100
  }'
```

### Health Check
```bash
curl http://localhost:11400/health
```

## Available Models

| Model | Type | Size | Memory | Port | Description |
|-------|------|------|--------|------|-------------|
| llama3 | Text | ~8B | 8GB | 11400 | Meta Llama 3 8B Instruct |
| mistral | Text | ~7B | 6GB | 11401 | Mistral 7B Instruct v0.2 |
| qwen2 | Text | ~7B | 8GB | 11402 | Qwen2 7B Instruct |
| moondream2 | Vision | ~2B | 6GB | 11403 | Vision-language model |
| deepseek | Text | ~7B | 6GB | 11404 | DeepSeek Coder 6.7B |
| granite | Text | ~8B | 8GB | 11405 | IBM Granite 3.0 8B |
| phi4 | Text | ~14B | 6GB | 11406 | Microsoft Phi-4 |

## Directory Structure

```
quoteGenie/
├── models/                      # Downloaded HF models (gitignored)
│   ├── llama3/
│   │   ├── config.json
│   │   ├── tokenizer.json
│   │   └── model.safetensors
│   ├── mistral/
│   └── ...
├── model_server/               # Custom model server
│   ├── Dockerfile              # Server container definition
│   ├── requirements.txt        # Python dependencies
│   └── server.py              # FastAPI server code
├── download_models.py         # Model download script
├── docker-compose.yml         # Main compose file
└── docker-compose.ai.yml      # Full AI stack
```

## Troubleshooting

### Model not found
```
Error: Model path does not exist: /model
```
**Solution:** Download the model first using `download_models.py`

### Out of memory
```
RuntimeError: CUDA out of memory
```
**Solution:** 
- Reduce models running simultaneously
- Increase Docker memory limits in Docker Desktop
- Use CPU instead (slower but works): Set `DEVICE=cpu` in environment

### Authentication required
```
Error: Repository not found or requires authentication
```
**Solution:**
1. Go to https://huggingface.co/settings/tokens
2. Create a token
3. Set `$env:HF_TOKEN="hf_your_token"` in PowerShell
4. Re-run download script

### Port already in use
```
Error: bind: address already in use
```
**Solution:** Change the port mapping in docker-compose.yml:
```yaml
ports:
  - "11410:11434"  # Use different host port
```

## Performance Tips

1. **Use GPU**: Ensure Docker Desktop has GPU access enabled
2. **Batch Downloads**: Download multiple models at once during off-peak hours
3. **SSD Storage**: Store models on SSD for faster loading
4. **Memory**: Allocate sufficient RAM in Docker Desktop (16GB+ recommended)
5. **Pruning**: Remove unused models to save disk space

## Disk Space Requirements

Approximate sizes after download:

- **Mistral 7B**: ~14 GB
- **Llama 3 8B**: ~16 GB
- **Qwen2 7B**: ~15 GB
- **Moondream2**: ~4 GB
- **DeepSeek**: ~13 GB
- **Granite 8B**: ~16 GB
- **Phi-4 14B**: ~28 GB

**Total for all models**: ~100-120 GB

## Advanced: Adding Custom Models

To add your own Hugging Face model:

1. **Update `download_models.py`:**
```python
MODEL_CONFIGS = {
    # ... existing models ...
    "my_model": {
        "repo_id": "username/model-name",
        "requires_auth": False,
        "description": "My custom model"
    }
}
```

2. **Add to `docker-compose.yml`:**
```yaml
my_model:
  build: ./model_server
  ports: ["11407:11434"]
  volumes:
    - ./models/my_model:/model:ro
  environment:
    - MODEL_PATH=/model
    - MODEL_TYPE=text  # or vision
    - PORT=11434
```

3. **Download and run:**
```powershell
python download_models.py --model my_model
docker-compose up my_model
```

## Migration from Ollama Registry

If you were previously using `ollama/llama3:latest` images:

**Old way:**
```yaml
llama3:
  image: ollama/llama3:latest  # Pulls from Docker Hub
  ports: ["11400:11400"]
```

**New way:**
```yaml
llama3:
  build: ./model_server           # Builds custom server
  volumes:
    - ./models/llama3:/model:ro  # Mounts local model
  ports: ["11400:11434"]
  environment:
    - MODEL_PATH=/model
```

## Next Steps

1. Download your first model: `python download_models.py --model mistral`
2. Test the server: `docker-compose up mistral`
3. Integrate with orchestrator: Update `orchestrator/router.py` endpoints
4. Scale up: Download additional models as needed

## Support

- **Hugging Face Issues**: https://github.com/huggingface/transformers/issues
- **Model Server Issues**: Check `docker-compose logs <service_name>`
- **Performance**: Monitor with `docker stats`

---

**🎉 You've successfully bypassed Docker registry and are running Hugging Face models directly!**
