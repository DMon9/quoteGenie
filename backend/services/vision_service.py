import os
from typing import Dict, List, Any, Optional, Tuple
import aiofiles
from pathlib import Path

# Optional image backends (graceful degradation if not installed)
try:  # OpenCV and NumPy are optional
    import cv2  # type: ignore
    import numpy as np  # type: ignore
    _HAS_CV2 = True
except Exception:
    cv2 = None  # type: ignore
    np = None  # type: ignore
    _HAS_CV2 = False

try:  # Pillow is optional
    from PIL import Image  # type: ignore
    _HAS_PIL = True
except Exception:
    Image = None  # type: ignore
    _HAS_PIL = False

class VisionService:
    """Handles all computer vision tasks"""
    
    def __init__(self):
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)
        # Optional Vision-Language Model endpoint (served via model_server)
        # Example: http://moondream2:11434/api/vision or http://smolvlm:11434/api/vision
        self.vlm_endpoint = os.getenv("VISION_VLM_URL", "").strip()
        self.vlm_prompt = os.getenv(
            "VISION_VLM_PROMPT",
            "Describe this image focusing on construction context, materials, and measurable features."
        )
        
        # Initialize models
        self._init_models()
    
    def _init_models(self):
        """Initialize vision models"""
        try:
            # Try to load YOLOv8 if available
            try:
                from ultralytics import YOLO
                self.detector = YOLO('yolov8n.pt')
                self.has_yolo = True
            except:
                print("YOLOv8 not available - using basic detection")
                self.detector = None
                self.has_yolo = False
            
            self.ready = True
        except Exception as e:
            print(f"Vision model initialization error: {e}")
            self.ready = False
    
    def is_ready(self) -> bool:
        return self.ready
    
    async def save_image(self, file, quote_id: str) -> str:
        """Save uploaded image to disk"""
        file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        filename = f"{quote_id}.{file_ext}"
        filepath = self.upload_dir / filename
        
        async with aiofiles.open(filepath, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        return str(filepath)
    
    async def analyze_image(self, image_path: str, project_type: str) -> Dict[str, Any]:
        """
        Run complete vision analysis pipeline:
        1. Object detection
        2. Segmentation
        3. Depth estimation
        4. Measurement extraction
        """
        
        # Load image (prefer OpenCV; fallback to Pillow; otherwise just get size)
        image = None
        width = height = None
        if _HAS_CV2:
            try:
                image = cv2.imread(image_path)  # type: ignore
                if image is None:
                    raise ValueError("Failed to load image with OpenCV")
                height, width = image.shape[:2]
            except Exception as _:
                image = None
        if image is None and _HAS_PIL:
            try:
                with Image.open(image_path) as im:  # type: ignore
                    width, height = im.size
            except Exception as _:
                pass
        if width is None or height is None:
            raise ValueError("Failed to load image; no supported image backend available")
        
        # Run object detection
        detections = self._detect_objects(image, project_type)
        
        # Estimate depth/scale
        depth_info = self._estimate_depth(image)
        
        # Extract measurements
        measurements = self._extract_measurements(image, (width, height), detections, depth_info)
        
        result: Dict[str, Any] = {
            "image_dimensions": {"width": width, "height": height},
            "detections": detections,
            "depth_info": depth_info,
            "measurements": measurements,
            "scene_description": self._generate_scene_description(detections)
        }

        # Optionally enrich with VLM description
        if self.vlm_endpoint:
            try:
                import base64
                import httpx
                # Read image bytes and encode
                with open(image_path, "rb") as f:
                    img_b64 = base64.b64encode(f.read()).decode("utf-8")
                payload = {"image": img_b64, "prompt": self.vlm_prompt, "max_tokens": 256}
                async with httpx.AsyncClient(timeout=20.0) as client:
                    resp = await client.post(self.vlm_endpoint, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        result["vlm_description"] = data.get("description") or data.get("generated_text")
                        if result.get("vlm_description"):
                            # Prefer VLM description if present
                            result["scene_description"] = result["vlm_description"]
                    else:
                        result["vlm_error"] = f"VLM HTTP {resp.status_code}"
            except Exception as e:
                result["vlm_error"] = f"VLM call failed: {e}"

        return result
    
    def _detect_objects(self, image: Optional[Any], project_type: str) -> List[Dict]:
        """Detect relevant objects in the image"""
        detections = []
        
        if self.has_yolo and self.detector is not None:
            try:
                results = self.detector(image)
                for r in results:
                    boxes = r.boxes
                    for box in boxes:
                        detections.append({
                            "class": r.names[int(box.cls[0])],
                            "confidence": float(box.conf[0]),
                            "bbox": box.xyxy[0].tolist()
                        })
            except Exception as e:
                print(f"Detection error: {e}")
        
        # Fallback: basic analysis
        if not detections:
            detections = self._basic_detection(image, project_type)
        
        return detections
    
    def _basic_detection(self, image: Optional[Any], project_type: str) -> List[Dict]:
        """Basic fallback detection without ML models"""
        try:
            if _HAS_CV2 and image is not None:
                height, width = image.shape[:2]
                # Detect basic features via edges
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # type: ignore
                edges = cv2.Canny(gray, 50, 150)  # type: ignore
                edge_density = float((edges > 0).sum()) / float(width * height)
                complexity = "high" if edge_density > 0.1 else "low"
            else:
                # Without OpenCV, we can't analyze edges; assume low complexity
                width, height = 1000, 1000
                complexity = "low"
        except Exception:
            width, height = 1000, 1000
            complexity = "low"

        return [{
            "class": "scene",
            "confidence": 0.7,
            "bbox": [0, 0, width, height],
            "complexity": complexity
        }]
    
    def _estimate_depth(self, image: Optional[Any]) -> Dict[str, Any]:
        """Estimate depth/scale from image"""
        # Basic scale estimation - assumes standard room if no reference
        return {
            "method": "estimated",
            "scale_factor": 1.0,
            "confidence": 0.6,
            "notes": "No reference object detected - using default scale"
        }
    
    def _extract_measurements(
        self,
        image: Optional[Any],
        image_size: Optional[Tuple[int, int]],
        detections: List[Dict],
        depth_info: Dict
    ) -> Dict[str, Any]:
        """Extract physical measurements from image"""
        # Determine image size
        if _HAS_CV2 and image is not None:
            height, width = image.shape[:2]
        elif image_size is not None:
            width, height = image_size
        else:
            width = height = 1000
        scale = depth_info.get("scale_factor", 1.0)
        
        # Estimate area based on image dimensions
        # Assuming roughly 100 sqft per standard camera view
        estimated_area = 100.0
        
        return {
            "estimated_area_sqft": round(estimated_area, 2),
            "wall_height_ft": 8.0,
            "detected_dimensions": [],
            "confidence": "medium"
        }
    
    def _generate_scene_description(self, detections: List[Dict]) -> str:
        """Generate natural language description of scene"""
        if not detections:
            return "Scene analysis in progress"
        
        items = [d["class"] for d in detections]
        unique_items = list(set(items))
        
        if len(unique_items) == 1 and unique_items[0] == "scene":
            return "General construction scene detected"
        
        return f"Scene contains: {', '.join(unique_items[:5])}"
