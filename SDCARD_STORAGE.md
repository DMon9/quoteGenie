# 💾 SD Card Storage Configuration

Your system is now configured to store Hugging Face models on the SD card (D:) instead of the main drive.

## Quick Setup

```powershell
# Run the setup script
.\setup_sdcard.ps1
```

This will:
- ✅ Create `D:\quoteGenie_models` directory
- ✅ Set `MODELS_DIR` environment variable
- ✅ Update `.env` file with the path
- ✅ Show available space and capacity

## Manual Configuration

If you prefer manual setup:

```powershell
# 1. Create directory on SD card
New-Item -ItemType Directory -Path "D:\quoteGenie_models" -Force

# 2. Set environment variable
$env:MODELS_DIR = "D:\quoteGenie_models"

# 3. Add to .env file (optional, for persistence)
Add-Content -Path .env -Value "MODELS_DIR=D:\quoteGenie_models"
```

## Usage

### Download Models to SD Card

```powershell
# Set the location (automatic if you ran setup_sdcard.ps1)
$env:MODELS_DIR = "D:\quoteGenie_models"

# Download a model
python download_models.py --model mistral

# List models and their location
python download_models.py --list
```

### Run Docker with SD Card Models

```powershell
# Set the location
$env:MODELS_DIR = "D:\quoteGenie_models"

# Run a specific model
docker-compose --profile models up mistral

# Run all models
docker-compose -f docker-compose.ai.yml up
```

## How It Works

The system uses Docker volume variable substitution:

```yaml
volumes:
  - ${MODELS_DIR:-./models}/mistral:/model:ro
```

- `${MODELS_DIR:-./models}` means: Use `MODELS_DIR` env var, or default to `./models`
- `/mistral:/model:ro` mounts as read-only inside container

## Directory Structure

```
D:\quoteGenie_models\          ← SD Card root
├── mistral\
│   ├── config.json
│   ├── model.safetensors
│   └── tokenizer.json
├── qwen2\
├── moondream2\
└── llama3\
```

## Space Management

Your SD card (D:) has approximately **54 GB** free space.

### Recommended Models for SD Card

| Model | Size | Purpose | Priority |
|-------|------|---------|----------|
| **mistral** | ~14 GB | General text generation | ⭐⭐⭐ High |
| **moondream2** | ~4 GB | Vision/image analysis | ⭐⭐⭐ High |
| **qwen2** | ~15 GB | Advanced reasoning | ⭐⭐ Medium |
| deepseek | ~13 GB | Code generation | ⭐ Low |

With 54 GB, you can comfortably fit **3-4 models**.

## Troubleshooting

### "Drive D: not found"
- Ensure SD card is properly inserted
- Check it's assigned drive letter D: in Windows Disk Management
- Try running: `Get-Volume | Format-Table`

### "Permission denied"
- Run PowerShell as Administrator
- Check SD card is not write-protected

### "No space left on device"
- Check free space: `Get-Volume D | Select-Object SizeRemaining`
- Remove unused models from SD card
- Consider using a larger SD card (128GB+ recommended)

### Docker can't find models
Make sure to set `MODELS_DIR` before running docker-compose:

```powershell
$env:MODELS_DIR = "D:\quoteGenie_models"
docker-compose up mistral
```

## Persistence

To make the setting permanent across PowerShell sessions:

```powershell
# Add to your PowerShell profile
notepad $PROFILE

# Add this line:
$env:MODELS_DIR = "D:\quoteGenie_models"

# Save and reload
. $PROFILE
```

## Performance Notes

- ✅ SD cards work fine for model loading (one-time read)
- ✅ Models are cached in container memory during inference
- ✅ Read-only mounts prevent accidental SD card writes
- ⚠️ Slightly slower initial load time vs SSD (acceptable)
- ⚠️ Make sure SD card has good read speeds (UHS-I or better)

## Migration from Local Storage

If you already downloaded models to `./models`:

```powershell
# Copy existing models to SD card
Copy-Item -Path ".\models\*" -Destination "D:\quoteGenie_models\" -Recurse

# Verify
python download_models.py --list
```

---

**✨ Your models are now on the SD card, freeing up your main drive!**
