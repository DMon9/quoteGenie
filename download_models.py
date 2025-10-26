"""
Download and cache Hugging Face models locally to bypass Docker registry.
This script downloads models directly from Hugging Face and stores them in the models/ directory.
"""

import os
from pathlib import Path
from huggingface_hub import snapshot_download
import argparse

# Storage configuration
# Set MODELS_DIR environment variable to use custom location (e.g., SD card)
# Default: ./models (current directory)
DEFAULT_MODELS_DIR = os.getenv("MODELS_DIR", "models")
MODELS_BASE_PATH = Path(DEFAULT_MODELS_DIR)

# Model configurations - map model names to HuggingFace repos
MODEL_CONFIGS = {
    "llama3": {
        "repo_id": "meta-llama/Meta-Llama-3-8B-Instruct",
        "requires_auth": True,
        "description": "Meta Llama 3 8B Instruct model"
    },
    "llama31": {
        "repo_id": "meta-llama/Meta-Llama-3.1-8B-Instruct",
        "requires_auth": True,
        "description": "Meta Llama 3.1 8B Instruct model"
    },
    "mistral": {
        "repo_id": "mistralai/Mistral-7B-Instruct-v0.2",
        "requires_auth": False,
        "description": "Mistral 7B Instruct v0.2"
    },
    "qwen2": {
        "repo_id": "Qwen/Qwen2-7B-Instruct",
        "requires_auth": False,
        "description": "Qwen2 7B Instruct"
    },
    "qwen25_0_5b": {
        "repo_id": "Qwen/Qwen2.5-0.5B-Instruct",
        "requires_auth": False,
        "description": "Qwen2.5 0.5B Instruct (tiny, SD-card friendly)"
    },
    "moondream2": {
        "repo_id": "vikhyatk/moondream2",
        "requires_auth": False,
        "description": "Moondream2 vision-language model"
    },
    "smolvlm": {
        "repo_id": "HuggingFaceTB/SmolVLM-Instruct",
        "requires_auth": False,
        "description": "SmolVLM Instruct (vision-language, lightweight)"
    },
    "deepseek": {
        "repo_id": "deepseek-ai/deepseek-coder-6.7b-instruct",
        "requires_auth": False,
        "description": "DeepSeek Coder 6.7B Instruct"
    },
    "granite": {
        "repo_id": "ibm-granite/granite-3.0-8b-instruct",
        "requires_auth": False,
        "description": "IBM Granite 3.0 8B Instruct"
    },
    "phi4": {
        "repo_id": "microsoft/phi-4",
        "requires_auth": False,
        "description": "Microsoft Phi-4"
    },
    "gemma2": {
        "repo_id": "google/gemma-2-9b-it",
        "requires_auth": True,
        "description": "Google Gemma 2 9B Instruct (may require EULA acceptance)"
    },
    "tinyllama": {
        "repo_id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "requires_auth": False,
        "description": "TinyLlama 1.1B Chat (very small, great for quick tests)"
    }
}

def download_model(model_name: str, force: bool = False):
    """Download a specific model from Hugging Face."""
    if model_name not in MODEL_CONFIGS:
        print(f"❌ Unknown model: {model_name}")
        print(f"Available models: {', '.join(MODEL_CONFIGS.keys())}")
        return False
    
    config = MODEL_CONFIGS[model_name]
    local_dir = MODELS_BASE_PATH / model_name
    
    print(f"\n{'='*60}")
    print(f"📦 Downloading: {model_name}")
    print(f"🏢 Repository: {config['repo_id']}")
    print(f"📝 Description: {config['description']}")
    print(f"📂 Local directory: {local_dir}")
    print(f"{'='*60}\n")
    
    # Check if model already exists
    if local_dir.exists() and not force and any(local_dir.iterdir()):
        print(f"✅ Model already exists at {local_dir}")
        print("   Use --force to re-download")
        return True
    
    # Create directory
    local_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Check for HF token if required
        hf_token = os.getenv("HF_TOKEN")
        if config["requires_auth"] and not hf_token:
            print(f"⚠️  Warning: {model_name} requires authentication")
            print("   Set HF_TOKEN environment variable with your Hugging Face token")
            print("   Get your token from: https://huggingface.co/settings/tokens")
            return False
        
        # Download the model
        print(f"⬇️  Downloading {config['repo_id']}...")
        print("   This may take a while depending on your internet connection...")
        
        snapshot_download(
            repo_id=config["repo_id"],
            local_dir=str(local_dir),
            token=hf_token if config["requires_auth"] else None,
            local_dir_use_symlinks=False,
            resume_download=True
        )
        
        print(f"\n✅ Successfully downloaded {model_name} to {local_dir}")
        return True
        
    except Exception as e:
        print(f"\n❌ Error downloading {model_name}: {str(e)}")
        return False

def list_models():
    """List all available models and their download status."""
    print("\n" + "="*80)
    print("📋 AVAILABLE MODELS")
    print("="*80)
    print(f"📂 Storage location: {MODELS_BASE_PATH.absolute()}")
    print("="*80 + "\n")
    
    for model_name, config in MODEL_CONFIGS.items():
        local_dir = MODELS_BASE_PATH / model_name
        exists = local_dir.exists() and any(local_dir.iterdir())
        status = "✅ Downloaded" if exists else "⬇️  Not downloaded"
        auth = "🔒 Requires auth" if config["requires_auth"] else "🔓 Public"
        
        print(f"{model_name:15} {status:20} {auth:20}")
        print(f"                {config['description']}")
        print(f"                {config['repo_id']}")
        print()

def main():
    parser = argparse.ArgumentParser(
        description="Download Hugging Face models for local use with Docker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=r"""
Examples:
  # List all available models
  python download_models.py --list
  
  # Download a specific model
  python download_models.py --model mistral
  
  # Download multiple models
  python download_models.py --model mistral --model qwen2
  
  # Download all models
  python download_models.py --all
  
  # Force re-download
  python download_models.py --model llama3 --force
  
  # Use SD card for storage (Windows)
  $env:MODELS_DIR="D:\quoteGenie_models"; python download_models.py --model mistral

Environment Variables:
  MODELS_DIR: Custom storage location (default: ./models)
              Example: D:\quoteGenie_models (SD card)
  HF_TOKEN:   Hugging Face API token (required for gated models like Llama 3)
              Get it from: https://huggingface.co/settings/tokens
        """
    )
    
    parser.add_argument(
        "--model", "-m",
        action="append",
        choices=list(MODEL_CONFIGS.keys()),
        help="Model to download (can be specified multiple times)"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Download all available models"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available models and their status"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force re-download even if model exists"
    )
    
    args = parser.parse_args()
    
    # List models
    if args.list:
        list_models()
        return
    
    # Determine which models to download
    models_to_download = []
    if args.all:
        models_to_download = list(MODEL_CONFIGS.keys())
    elif args.model:
        models_to_download = args.model
    else:
        parser.print_help()
        return
    
    # Download models
    print("\n🚀 Starting model downloads...\n")
    results = {}
    
    for model in models_to_download:
        results[model] = download_model(model, force=args.force)
    
    # Summary
    print("\n" + "="*60)
    print("📊 DOWNLOAD SUMMARY")
    print("="*60)
    
    successful = [m for m, r in results.items() if r]
    failed = [m for m, r in results.items() if not r]
    
    if successful:
        print(f"\n✅ Successfully downloaded ({len(successful)}):")
        for model in successful:
            print(f"   - {model}")
    
    if failed:
        print(f"\n❌ Failed to download ({len(failed)}):")
        for model in failed:
            print(f"   - {model}")
    
    print("\n" + "="*60)
    print("\n💡 Next steps:")
    print("   1. Run: docker-compose up orchestrator")
    print("   2. Models will be mounted from ./models/ directory")
    print("   3. No Docker registry pulls required!")
    print()

if __name__ == "__main__":
    main()
