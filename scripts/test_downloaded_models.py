"""
Test downloaded HuggingFace models without Docker.

Loads models directly from disk (MODELS_DIR) and runs a quick generation test
to confirm each model is functional. Useful for validating downloads before
building Docker images.

Usage:
    D:/sd/Scripts/python.exe scripts/test_downloaded_models.py --model tinyllama
    D:/sd/Scripts/python.exe scripts/test_downloaded_models.py --all
"""

import argparse
import json
import os
import time
from pathlib import Path
from typing import Optional

MODELS_DIR = os.getenv("MODELS_DIR", "models")
MODELS_BASE = Path(MODELS_DIR)

TEST_PROMPT = "Hello! Please respond with 'OK' to confirm you are working."

# Known models from download_models.py
AVAILABLE_MODELS = [
    "llama3", "llama31", "mistral", "qwen2", "qwen25_0_5b",
    "moondream2", "deepseek", "granite", "phi4", "gemma2", "tinyllama"
]


def test_text_model(model_path: Path, model_name: str) -> dict:
    """Test a text generation model."""
    print(f"\n{'='*60}")
    print(f"Testing: {model_name}")
    print(f"Path: {model_path}")
    print(f"{'='*60}\n")
    
    if not model_path.exists():
        return {
            "model": model_name,
            "status": "NOT_DOWNLOADED",
            "error": f"Model directory not found: {model_path}"
        }
    
    try:
        # Try to import transformers
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Device: {device}")
        
        # Load tokenizer
        print("Loading tokenizer...")
        t0 = time.perf_counter()
        tokenizer = AutoTokenizer.from_pretrained(str(model_path))
        t_tokenizer = time.perf_counter() - t0
        print(f"✅ Tokenizer loaded in {t_tokenizer:.2f}s")
        
        # Load model
        print("Loading model...")
        t0 = time.perf_counter()
        model = AutoModelForCausalLM.from_pretrained(
            str(model_path),
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map="auto" if device == "cuda" else None,
            low_cpu_mem_usage=True
        )
        if device == "cpu":
            model = model.to(device)
        t_model = time.perf_counter() - t0
        print(f"✅ Model loaded in {t_model:.2f}s")
        
        # Generate
        print(f"\nPrompt: {TEST_PROMPT}")
        t0 = time.perf_counter()
        inputs = tokenizer(TEST_PROMPT, return_tensors="pt").to(device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=32,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        if response.startswith(TEST_PROMPT):
            response = response[len(TEST_PROMPT):].strip()
        
        t_gen = time.perf_counter() - t0
        print(f"\n✅ Generated in {t_gen:.2f}s:")
        print(f"   {response[:200]}")
        
        return {
            "model": model_name,
            "status": "PASS",
            "device": device,
            "load_time_s": round(t_tokenizer + t_model, 2),
            "gen_time_s": round(t_gen, 2),
            "response_preview": response[:100]
        }
        
    except ImportError as e:
        return {
            "model": model_name,
            "status": "MISSING_DEPS",
            "error": f"Missing dependency: {e}. Install: pip install transformers torch"
        }
    except Exception as e:
        return {
            "model": model_name,
            "status": "FAIL",
            "error": str(e)
        }


def test_vision_model(model_path: Path, model_name: str) -> dict:
    """Test a vision-language model (moondream2)."""
    print(f"\n{'='*60}")
    print(f"Testing vision model: {model_name}")
    print(f"Path: {model_path}")
    print(f"{'='*60}\n")
    
    if not model_path.exists():
        return {
            "model": model_name,
            "status": "NOT_DOWNLOADED",
            "error": f"Model directory not found: {model_path}"
        }
    
    return {
        "model": model_name,
        "status": "SKIP",
        "error": "Vision model testing requires image input—use healthcheck_models.py with Docker"
    }


def list_downloaded_models() -> list:
    """List all downloaded models."""
    downloaded = []
    for model_name in AVAILABLE_MODELS:
        model_path = MODELS_BASE / model_name
        if model_path.exists() and any(model_path.iterdir()):
            downloaded.append(model_name)
    return downloaded


def main():
    parser = argparse.ArgumentParser(
        description="Test downloaded HuggingFace models without Docker"
    )
    parser.add_argument(
        "--model", "-m",
        help="Model to test (e.g., tinyllama)"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Test all downloaded models"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List downloaded models"
    )
    
    args = parser.parse_args()
    
    # List
    if args.list:
        downloaded = list_downloaded_models()
        print(f"\nDownloaded models in {MODELS_BASE}:")
        for m in downloaded:
            print(f"  - {m}")
        print(f"\nTotal: {len(downloaded)}")
        return
    
    # Determine which to test
    models_to_test = []
    if args.all:
        models_to_test = list_downloaded_models()
    elif args.model:
        if args.model not in AVAILABLE_MODELS:
            print(f"❌ Unknown model: {args.model}")
            print(f"Available: {', '.join(AVAILABLE_MODELS)}")
            return
        models_to_test = [args.model]
    else:
        parser.print_help()
        return
    
    if not models_to_test:
        print(f"No models found to test. Download models first with:")
        print(f"  D:/sd/Scripts/python.exe download_models.py --model tinyllama")
        return
    
    # Test each
    results = []
    for model_name in models_to_test:
        model_path = MODELS_BASE / model_name
        
        # Determine model type
        if model_name == "moondream2":
            result = test_vision_model(model_path, model_name)
        else:
            result = test_text_model(model_path, model_name)
        
        results.append(result)
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = [r for r in results if r["status"] == "PASS"]
    failed = [r for r in results if r["status"] == "FAIL"]
    skipped = [r for r in results if r["status"] == "SKIP"]
    not_downloaded = [r for r in results if r["status"] == "NOT_DOWNLOADED"]
    
    if passed:
        print(f"\n✅ PASSED ({len(passed)}):")
        for r in passed:
            print(f"   - {r['model']} (device={r['device']}, load={r['load_time_s']}s, gen={r['gen_time_s']}s)")
    
    if skipped:
        print(f"\n⏩ SKIPPED ({len(skipped)}):")
        for r in skipped:
            print(f"   - {r['model']}: {r.get('error', 'N/A')}")
    
    if not_downloaded:
        print(f"\n⬇️  NOT DOWNLOADED ({len(not_downloaded)}):")
        for r in not_downloaded:
            print(f"   - {r['model']}")
    
    if failed:
        print(f"\n❌ FAILED ({len(failed)}):")
        for r in failed:
            print(f"   - {r['model']}: {r.get('error', 'Unknown error')}")
    
    print(f"\nTotal: {len(results)} tested, {len(passed)} passed")
    print("\n💡 To test with Docker:")
    print("   docker-compose --profile models up tinyllama")
    print("   D:/sd/Scripts/python.exe scripts/healthcheck_models.py")


if __name__ == "__main__":
    main()
