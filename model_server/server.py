"""
Generic model server for Hugging Face models.
Loads models from mounted volume and serves them via FastAPI.
"""

import os
import json
import base64
from io import BytesIO
from typing import Optional, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    AutoProcessor,
    AutoModelForVision2Seq,
    pipeline
)
from PIL import Image

# Environment configuration
MODEL_PATH = os.getenv("MODEL_PATH", "/model")
MODEL_TYPE = os.getenv("MODEL_TYPE", "text")  # text, vision, or auto-detect
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "11434"))
MAX_LENGTH = int(os.getenv("MAX_LENGTH", "2048"))
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

app = FastAPI(title="HuggingFace Model Server")

# Global model and tokenizer
model = None
tokenizer = None
processor = None
model_type = None


class TextRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9


class VisionRequest(BaseModel):
    image: str  # base64 encoded
    prompt: Optional[str] = "Describe this image in detail."
    max_tokens: Optional[int] = 512


def detect_model_type(model_path: Path) -> str:
    """Auto-detect model type from config.json."""
    config_path = model_path / "config.json"
    if not config_path.exists():
        return "text"
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check architecture
        architectures = config.get("architectures", [])
        if any("Vision" in arch for arch in architectures):
            return "vision"
        elif any("Causal" in arch or "LM" in arch for arch in architectures):
            return "text"
        
        # Check for image processor
        if (model_path / "preprocessor_config.json").exists():
            return "vision"
        
        return "text"
    except Exception as e:
        print(f"Error detecting model type: {e}")
        return "text"


def load_model():
    """Load the model from the mounted volume."""
    global model, tokenizer, processor, model_type
    
    model_path = Path(MODEL_PATH)
    
    if not model_path.exists():
        raise RuntimeError(f"Model path does not exist: {MODEL_PATH}")
    
    # Detect model type
    model_type = MODEL_TYPE if MODEL_TYPE != "auto" else detect_model_type(model_path)
    
    print(f"Loading {model_type} model from {MODEL_PATH}...")
    print(f"Using device: {DEVICE}")
    
    try:
        if model_type == "vision":
            # Load vision-language model
            processor = AutoProcessor.from_pretrained(str(model_path))
            model = AutoModelForVision2Seq.from_pretrained(
                str(model_path),
                torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
                device_map="auto" if DEVICE == "cuda" else None,
                low_cpu_mem_usage=True
            )
        else:
            # Load text model
            tokenizer = AutoTokenizer.from_pretrained(str(model_path))
            model = AutoModelForCausalLM.from_pretrained(
                str(model_path),
                torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
                device_map="auto" if DEVICE == "cuda" else None,
                low_cpu_mem_usage=True
            )
        
        if DEVICE == "cpu":
            model = model.to(DEVICE)
        
        model.eval()
        print(f"✅ Model loaded successfully on {DEVICE}")
        
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        raise


@app.on_event("startup")
async def startup_event():
    """Load model on startup."""
    load_model()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model_path": MODEL_PATH,
        "model_type": model_type,
        "device": DEVICE,
        "model_loaded": model is not None
    }


@app.post("/api/generate")
async def generate_text(request: TextRequest):
    """Generate text from a prompt."""
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    if model_type != "text":
        raise HTTPException(status_code=400, detail="This endpoint requires a text model")
    
    try:
        # Tokenize input
        inputs = tokenizer(
            request.prompt,
            return_tensors="pt",
            truncation=True,
            max_length=MAX_LENGTH
        ).to(DEVICE)
        
        # Generate
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        # Decode
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Remove the prompt from output
        if generated_text.startswith(request.prompt):
            generated_text = generated_text[len(request.prompt):].strip()
        
        return {
            "generated_text": generated_text,
            "model": MODEL_PATH,
            "device": DEVICE
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")


@app.post("/api/vision")
async def analyze_image(request: VisionRequest):
    """Analyze an image with vision-language model."""
    if model is None or processor is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    if model_type != "vision":
        raise HTTPException(status_code=400, detail="This endpoint requires a vision model")
    
    try:
        # Decode base64 image
        image_data = base64.b64decode(request.image)
        image = Image.open(BytesIO(image_data)).convert("RGB")
        
        # Process inputs
        inputs = processor(
            text=request.prompt,
            images=image,
            return_tensors="pt"
        ).to(DEVICE)
        
        # Generate
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                do_sample=False
            )
        
        # Decode
        generated_text = processor.batch_decode(outputs, skip_special_tokens=True)[0]
        
        return {
            "description": generated_text,
            "model": MODEL_PATH,
            "device": DEVICE
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vision analysis error: {str(e)}")


@app.post("/api/chat")
async def chat(request: TextRequest):
    """Chat endpoint compatible with OpenAI-style requests."""
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Format as chat if tokenizer supports it
        if hasattr(tokenizer, "apply_chat_template"):
            messages = [{"role": "user", "content": request.prompt}]
            formatted_prompt = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
        else:
            formatted_prompt = request.prompt
        
        # Generate using the text generation endpoint
        response = await generate_text(
            TextRequest(
                prompt=formatted_prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p
            )
        )
        
        return {
            "message": response["generated_text"],
            "model": MODEL_PATH
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


if __name__ == "__main__":
    print(f"Starting model server on {HOST}:{PORT}")
    print(f"Model path: {MODEL_PATH}")
    print(f"Model type: {MODEL_TYPE}")
    
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info"
    )
