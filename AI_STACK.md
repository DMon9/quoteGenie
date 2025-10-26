# EstimateGenie AI Stack Architecture

Complete technical blueprint for building the vision + reasoning backend that powers EstimateGenie's AI estimation engine.

---

## 🧠 1. CORE AI LAYERS (VISION + REASONING)

| Category | Component | Description | Notes |
|----------|-----------|-------------|-------|
| **Vision (Perception)** | GroundingDINO | Object detection + segmentation + natural language grounding | Excellent for construction, damage, and material detection |
| | Segment Anything (SAM) | General-purpose segmentation model from Meta | Use it to isolate materials, tools, or damaged areas |
| | Depth Anything / MiDaS | Depth estimation model | Estimates scale/distance for accurate measurements |
| | YOLOv8 / YOLO-NAS | Lightweight detector for fast inference | Ideal for edge devices (Jetson, Pi, etc.) |
| **3D & Measurement** | OpenMVS / COLMAP | Converts multiple photos into a 3D model or point cloud | Used to estimate area, volume, or distance |
| **Vision Reasoning (Multimodal)** | LLaVA-OneVision or Qwen2-VL | Vision-language model that can describe, reason, and interpret images | Use for reasoning about detected elements: "what's needed to fix this?" |
| **Language Reasoning** | OpenHermes 2.5, Mistral 7B, or Llama 3 8B Instruct | Core text reasoning for generating structured output (estimate breakdown, materials, etc.) | Run locally or via API |
| **Chain Reasoning Framework** | LangChain or LlamaIndex | Connects multiple models and logic chains | Handles routing between vision and language tasks |

---

## 🧩 2. DATA PIPELINE & PARSING

| Category | Component | Description |
|----------|-----------|-------------|
| **Image Preprocessing** | OpenCV + Pillow | Resize, crop, and enhance photos before analysis |
| **Annotation / Labeling** | CVAT or Label Studio | Optional: manually label images to improve detection |
| **Scene Description Extraction** | BLIP-2 + LLaVA | Generates contextual descriptions from photos |
| **Feature Vector Storage** | FAISS or Chroma | Stores embeddings for image similarity and re-use |
| **Structured Output Formatting** | Pydantic or JSON schema | Enforces clean structured data for estimates |
| **Natural Language → Structured Data** | GPT4All function calling / OpenDevin | Converts free text reasoning into cost tables and material lists |

---

## ⚙️ 3. INFRASTRUCTURE + BACKEND

| Category | Component | Description |
|----------|-----------|-------------|
| **API Gateway** | FastAPI or BentoML | Lightweight serving layer for your models |
| **Model Hosting** | Ollama or vLLM | Run LLMs locally with GPU acceleration |
| **Job Orchestration** | Ray or Celery | Handles multi-model pipelines and async task flow |
| **Database** | PostgreSQL / SQLite | Store past estimates, jobs, materials |
| **File Storage** | MinIO / Local FS / S3-compatible | Store photos, 3D data, and outputs |
| **Compute Hardware** | NVIDIA RTX 4060+ / Jetson Orin / AMD ROCm | Required for fast vision model inference |

---

## 🧰 4. ESTIMATION & DOMAIN LOGIC

| Layer | Component | Description |
|-------|-----------|-------------|
| **Quantity Takeoff** | Custom Python module using OpenCV + depth maps | Calculates approximate surface area or material volume |
| **Material Cost Lookup** | CSV/JSON + live APIs (e.g., Home Depot, Lowe's) | Auto-fetch current prices |
| **Labor Rate Engine** | Config file (hourly + difficulty multipliers) | Dynamically adjust labor cost |
| **Rule Engine** | OpenRules or Python logic | Define business rules (minimum charge, safety factors, etc.) |
| **Result Formatter** | Markdown or PDF template (ReportLab) | Produces clean customer-facing estimate |

---

## 🖥️ 5. FRONTEND / INTERFACE OPTIONS

| Component | Description |
|-----------|-------------|
| **Web Dashboard** | React + Next.js + FastAPI backend |
| **Mobile Upload App** | Flutter or React Native app for uploading project photos |
| **Command-Line Tool** | CLI for testing: `estimate image.jpg --type "roof repair"` |
| **Visualization Layer** | Streamlit or Gradio |

---

## 🧩 6. OPTIONAL AUGMENTATIONS

| Add-On | Description |
|--------|-------------|
| **AR Measurement Integration** | Integrate with ARKit/ARCore for on-site dimension capture |
| **Voice Interaction** | Use Whisper (ASR) + TTS models for voice-based inspection reports |
| **Prediction Enhancement** | Fine-tune YOLO/SAM on local dataset of your job types |
| **Offline Capability** | Bundle models with Ollama or LM Studio for local inference without internet |
| **Project Export** | Generate PDF, CSV, and full job summary in one click |

---

## 🔗 7. PIPELINE FLOW OVERVIEW

```
1. Input: User uploads image or short video
   ↓
2. Vision Stage: YOLO/SAM detect regions → Depth Anything measures scale → BLIP/LLaVA describes scene
   ↓
3. Reasoning Stage: LLM analyzes detected data → maps to materials, labor, and steps
   ↓
4. Estimation Stage: Cost engine compiles unit rates → applies labor rules and markup
   ↓
5. Output Stage: Generates formatted estimate report + material list + recommended workflow
```

---

## ⚡ 8. DEPLOYMENT OPTIONS

| Type | Description |
|------|-------------|
| **Local Edge** | Jetson Orin / mini PC with Ollama, FastAPI |
| **Cloud Hybrid** | Vision models on local GPU + reasoning via API |
| **Full Cloud** | Run everything on AWS (SageMaker, EC2 + S3 + Lambda) |
| **Containerized** | Docker Compose with FastAPI + Ollama + LangChain + MinIO stack |

---

## ✅ 9. MINIMUM VIABLE STACK (Starter Build)

If you want to get started today, build this lightweight version:

| Function | Tool |
|----------|------|
| **Vision Detection** | GroundingDINO + SAM |
| **Scene Reasoning** | LLaVA (Ollama) |
| **Output Formatting** | LangChain JSON output |
| **Backend** | FastAPI |
| **Frontend** | Streamlit |
| **Storage** | SQLite + Local FS |
| **Hardware** | 1x RTX 4060 or better |

---

## 🚀 10. GETTING STARTED

### Step 1: Install Dependencies

```bash
# Core Python environment
pip install fastapi uvicorn pydantic openai pillow opencv-python

# Vision models
pip install transformers torch torchvision ultralytics

# LangChain for orchestration
pip install langchain langchain-community

# Ollama for local LLM hosting
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llava
ollama pull llama3
```

### Step 2: Set Up FastAPI Backend

```python
# app.py
from fastapi import FastAPI, UploadFile
from pydantic import BaseModel

app = FastAPI()

@app.post("/estimate")
async def create_estimate(file: UploadFile):
    # 1. Save image
    # 2. Run vision models
    # 3. Run reasoning LLM
    # 4. Return structured estimate
    return {"status": "processing"}
```

### Step 3: Run Detection Pipeline

```python
# vision.py
from transformers import pipeline
import cv2

detector = pipeline("object-detection", model="IDEA-Research/grounding-dino-base")

def detect_objects(image_path):
    results = detector(image_path, candidate_labels=["wall", "door", "window", "fixture"])
    return results
```

### Step 4: Deploy

```bash
# Local development
uvicorn app:app --reload

# Production with Docker
docker build -t estimategenie-api .
docker run -p 8000:8000 estimategenie-api
```

---

## 📚 Additional Resources

- [GroundingDINO GitHub](https://github.com/IDEA-Research/GroundingDINO)
- [Segment Anything (SAM)](https://github.com/facebookresearch/segment-anything)
- [LLaVA Model](https://llava-vl.github.io/)
- [Ollama Documentation](https://ollama.com/docs)
- [LangChain Docs](https://python.langchain.com/)
- [FastAPI Guide](https://fastapi.tiangolo.com/)

---

## 🔧 Integration with EstimateGenie Frontend

This AI stack powers the backend API that the EstimateGenie web dashboard (hosted on Cloudflare Pages) calls when users upload project photos. The frontend sends images to:

```
POST https://api.estimategenie.net/v1/quotes
```

The backend processes images through the vision → reasoning → estimation pipeline and returns a structured quote object that the frontend displays.

---

## 📝 Next Steps

1. Set up a local development environment with the Minimum Viable Stack
2. Fine-tune detection models on your specific use cases (construction, damage assessment, etc.)
3. Build a cost database for materials and labor in your region
4. Deploy the API backend and connect it to the EstimateGenie frontend
5. Add monitoring and logging for production reliability

---

**Need help implementing any component? See DEPLOY_CLOUDFLARE.md for frontend hosting, or reach out for backend deployment guidance.**
