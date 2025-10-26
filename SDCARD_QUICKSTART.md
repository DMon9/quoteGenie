# Quick Start: SD Card Storage

## ✅ SD Card Configuration Complete!

Your models will now be stored on the SD card at: `D:\quoteGenie_models`

## Download Your First Model

```powershell
# Mistral is recommended (14GB, no auth required)
python download_models.py --model mistral
```

## Run with Docker

```powershell
# Make sure environment is set
$env:MODELS_DIR = "D:\quoteGenie_models"

# Run the model
docker-compose --profile models up mistral
```

## Available Space

SD Card D: has approximately **54 GB** free space
- Can fit 3-4 medium-sized models comfortably

## Recommended Models to Download

1. **mistral** (~14 GB) - Best general-purpose model
2. **moondream2** (~4 GB) - Vision/image analysis  
3. **qwen2** (~15 GB) - Advanced reasoning

Total: ~33 GB (leaves room for Docker images)

## Commands Reference

```powershell
# List all models and their status
python download_models.py --list

# Download specific model
python download_models.py --model mistral

# Download multiple models
python download_models.py --model mistral --model moondream2

# Run with Docker
$env:MODELS_DIR = "D:\quoteGenie_models"
docker-compose --profile models up mistral qwen2

# Check what's downloaded
dir D:\quoteGenie_models
```

## Persistence

The `MODELS_DIR` setting is saved in `.env` file, so Docker Compose will automatically use it.

For PowerShell sessions, set it each time or add to your profile:
```powershell
# Add to PowerShell profile (optional)
notepad $PROFILE
# Add line: $env:MODELS_DIR = "D:\quoteGenie_models"
```

## Next Steps

1. Download mistral: `python download_models.py --model mistral`
2. Test it works: `docker-compose --profile models up mistral`
3. Access API: `http://localhost:11401/health`

For full documentation, see `SDCARD_STORAGE.md`
