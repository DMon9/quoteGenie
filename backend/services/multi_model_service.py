"""
Multi-Model AI Service
Supports Gemini, GPT-4 Vision, and Claude 3 with intelligent fallback
"""
import os
import json
import base64
import asyncio
from typing import Dict, Any, List, Optional, Literal
from pathlib import Path

ModelType = Literal["gemini", "gpt4v", "claude", "auto"]

class MultiModelService:
    """Unified interface for multiple AI vision and reasoning models"""
    
    def __init__(self):
        # API Keys
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        # OpenRouter (for models like openai/gpt-oss-20b)
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        
        # Model configurations
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        self.gpt4v_model = os.getenv("GPT4V_MODEL", "gpt-4o")  # gpt-4o has vision
        self.claude_model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b")
        
        # Check availability
        self.available_models = self._check_available_models()
        self.preferred_model = os.getenv("PREFERRED_MODEL", "auto").lower()
        
        print(f"Multi-Model Service initialized. Available: {self.available_models}")
    
    def _check_available_models(self) -> List[str]:
        """Check which models are available based on API keys"""
        available = []
        if self.google_api_key and self.google_api_key != "your-google-api-key-here":
            available.append("gemini")
        if self.openai_api_key and self.openai_api_key != "your-openai-api-key-here":
            available.append("gpt4v")
        if self.anthropic_api_key and self.anthropic_api_key != "your-anthropic-api-key-here":
            available.append("claude")
        if self.openrouter_api_key and self.openrouter_api_key != "your-openrouter-api-key-here":
            available.append("gpt-oss-20b")
        return available
    
    def is_ready(self) -> bool:
        """Check if at least one model is available"""
        return len(self.available_models) > 0
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models with metadata"""
        models = []
        
        if "gemini" in self.available_models:
            models.append({
                "id": "gemini",
                "name": "Google Gemini 2.0 Flash",
                "provider": "google",
                "capabilities": ["vision", "reasoning", "fast"],
                "best_for": "General purpose, fast responses"
            })
        
        if "gpt4v" in self.available_models:
            models.append({
                "id": "gpt4v",
                "name": "OpenAI GPT-4 Vision",
                "provider": "openai",
                "capabilities": ["vision", "reasoning", "detailed"],
                "best_for": "Detailed analysis, complex reasoning"
            })
        
        if "claude" in self.available_models:
            models.append({
                "id": "claude",
                "name": "Anthropic Claude 3.5 Sonnet",
                "provider": "anthropic",
                "capabilities": ["vision", "reasoning", "precise"],
                "best_for": "Precise measurements, technical analysis"
            })

        if "gpt-oss-20b" in self.available_models:
            models.append({
                "id": "gpt-oss-20b",
                "name": "OpenAI GPT-OSS 20B (via OpenRouter)",
                "provider": "openrouter",
                "capabilities": ["reasoning", "cost-effective"],
                "best_for": "Cost-effective structured reasoning (text-only)"
            })
        
        return models
    
    async def analyze_construction_image(
        self,
        image_path: str,
        project_type: str,
        description: str = "",
        model: ModelType = "auto",
        vision_results: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Analyze construction image using AI models
        
        Args:
            image_path: Path to the image file
            project_type: Type of project (bathroom, kitchen, etc)
            description: User-provided description
            model: Which model to use ("gemini", "gpt4v", "claude", or "auto")
            vision_results: Optional pre-computed vision analysis results
        
        Returns:
            Analysis results with materials, labor estimates, etc.
        """
        
        # Read and encode image
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        # Build prompt
        prompt = self._build_analysis_prompt(project_type, description, vision_results)
        
        # Select model
        selected_model = self._select_model(model)
        
        # Try models with fallback
        models_to_try = [selected_model] if selected_model != "auto" else self.available_models
        
        last_error = None
        for model_name in models_to_try:
            try:
                print(f"Trying model: {model_name}")
                
                if model_name == "gemini":
                    result = await self._call_gemini(image_data, prompt)
                elif model_name == "gpt4v":
                    result = await self._call_gpt4v(image_data, prompt)
                elif model_name == "claude":
                    result = await self._call_claude(image_data, prompt)
                elif model_name == "gpt-oss-20b":
                    # Text-only: use prompt enriched with vision results, no image upload
                    result = await self._call_openrouter_text(prompt)
                else:
                    continue
                
                # Parse and return result
                parsed = self._parse_response(result, model_name)
                parsed["model_used"] = model_name
                return parsed
                
            except Exception as e:
                print(f"Model {model_name} failed: {e}")
                last_error = e
                continue
        
        # All models failed - return fallback
        print("All models failed, using fallback")
        return self._fallback_response(project_type, str(last_error))
    
    def _select_model(self, requested: ModelType) -> str:
        """Select which model to use"""
        if requested == "auto":
            # Auto-select based on preference and availability
            if self.preferred_model in self.available_models:
                return self.preferred_model
            # Default priority: gemini -> gpt4v -> claude
            if "gemini" in self.available_models:
                return "gemini"
            elif "gpt4v" in self.available_models:
                return "gpt4v"
            elif "claude" in self.available_models:
                return "claude"
            elif "gpt-oss-20b" in self.available_models:
                return "gpt-oss-20b"
            return "auto"
        
        # Check if requested model is available
        if requested in self.available_models:
            return requested
        
        # Fallback to auto if requested model not available
        print(f"Requested model {requested} not available, falling back")
        return "auto"
    
    def _build_analysis_prompt(
        self,
        project_type: str,
        description: str,
        vision_results: Optional[Dict]
    ) -> str:
        """Build analysis prompt for AI models"""
        
        prompt = f"""You are an expert construction estimator analyzing a {project_type} project.

Analyze this construction image and provide a detailed estimate.

"""
        
        if description:
            prompt += f"Project Description: {description}\n\n"
        
        if vision_results:
            detections = vision_results.get("detections", [])
            measurements = vision_results.get("measurements", {})
            prompt += f"""Computer Vision Analysis:
- Detected objects: {[d.get('class') for d in detections]}
- Estimated area: {measurements.get('estimated_area_sqft', 'unknown')} sq ft
- Scene: {vision_results.get('scene_description', 'unclear')}

"""
        
        prompt += """Please analyze the image and provide:

1. **Materials List**: Specific materials needed with quantities and units
2. **Labor Estimate**: Hours required for completion
3. **Challenges**: Potential issues or risks
4. **Approach**: Step-by-step recommended approach
5. **Cost Factors**: Key factors that affect pricing

Respond in JSON format:
{
  "materials": [
    {"name": "material name", "quantity": "amount", "unit": "unit", "notes": "optional notes"}
  ],
  "labor_hours": number,
  "labor_breakdown": {
    "demo": hours,
    "installation": hours,
    "finishing": hours
  },
  "challenges": ["challenge 1", "challenge 2"],
  "approach": "detailed step-by-step approach",
  "cost_factors": ["factor 1", "factor 2"],
  "measurements": {
    "estimated_sqft": number,
    "ceiling_height": number,
    "complexity": "low/medium/high"
  }
}

Focus on accuracy and provide realistic estimates based on what you see in the image.
"""
        
        return prompt
    
    async def _call_gemini(self, image_data: str, prompt: str) -> str:
        """Call Google Gemini Vision API"""
        
        def run_sync():
            import google.generativeai as genai
            genai.configure(api_key=self.google_api_key)
            model = genai.GenerativeModel(self.gemini_model)
            
            # Decode base64 to bytes for Gemini
            import base64
            image_bytes = base64.b64decode(image_data)
            
            # Create image part
            image_part = {
                "mime_type": "image/jpeg",
                "data": image_bytes
            }
            
            response = model.generate_content([prompt, image_part])
            return response.text
        
        return await asyncio.to_thread(run_sync)
    
    async def _call_gpt4v(self, image_data: str, prompt: str) -> str:
        """Call OpenAI GPT-4 Vision API"""
        import httpx
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.gpt4v_model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_data}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 2000
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
            
            result = response.json()
            return result["choices"][0]["message"]["content"]

    async def _call_openrouter_text(self, prompt: str) -> str:
        """Call OpenRouter text model (e.g., openai/gpt-oss-20b)."""
        import httpx

        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            # Optional but recommended by OpenRouter for analytics
            "HTTP-Referer": os.getenv("OPENROUTER_REFERRER", "https://estimategenie.net"),
            "X-Title": os.getenv("OPENROUTER_TITLE", "EstimateGenie")
        }

        payload = {
            "model": self.openrouter_model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 2000,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            if resp.status_code != 200:
                raise Exception(f"OpenRouter API error: {resp.status_code} - {resp.text}")
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    
    async def _call_claude(self, image_data: str, prompt: str) -> str:
        """Call Anthropic Claude Vision API"""
        import httpx
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.claude_model,
                    "max_tokens": 2000,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/jpeg",
                                        "data": image_data
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                            ]
                        }
                    ]
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Claude API error: {response.status_code} - {response.text}")
            
            result = response.json()
            return result["content"][0]["text"]
    
    def _parse_response(self, response: str, model: str) -> Dict[str, Any]:
        """Parse model response into structured format"""
        try:
            # Clean markdown code blocks
            cleaned = response.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
            
            data = json.loads(cleaned)
            
            # Ensure all required fields exist
            result = {
                "materials": data.get("materials", []),
                "labor_hours": data.get("labor_hours", 0),
                "labor_breakdown": data.get("labor_breakdown", {}),
                "challenges": data.get("challenges", []),
                "approach": data.get("approach", ""),
                "cost_factors": data.get("cost_factors", []),
                "measurements": data.get("measurements", {}),
                "raw_response": response,
                "model": model
            }
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON from {model}: {e}")
            print(f"Response: {response[:500]}")
            
            # Try to extract partial data
            return {
                "materials": [],
                "labor_hours": 0,
                "challenges": ["Unable to fully parse AI response"],
                "approach": response[:500],
                "raw_response": response,
                "model": model,
                "parse_error": str(e)
            }
    
    def _fallback_response(self, project_type: str, error: str = "") -> Dict[str, Any]:
        """Fallback response when all models fail"""
        
        templates = {
            "bathroom": {
                "materials": [
                    {"name": "Ceramic tile", "quantity": "50", "unit": "sqft"},
                    {"name": "Grout", "quantity": "2", "unit": "bags"},
                    {"name": "Tile adhesive", "quantity": "1", "unit": "bucket"},
                    {"name": "Waterproof membrane", "quantity": "50", "unit": "sqft"}
                ],
                "labor_hours": 24,
                "labor_breakdown": {"demo": 4, "installation": 16, "finishing": 4},
                "challenges": ["Requires plumbing work", "Waterproofing critical", "Precise tile cutting needed"],
                "approach": "1. Remove old fixtures and tile\n2. Install waterproof membrane\n3. Tile installation with proper spacing\n4. Grouting and sealing\n5. Fixture reinstallation",
                "cost_factors": ["Tile quality", "Plumbing modifications", "Custom vs standard fixtures"],
                "measurements": {"estimated_sqft": 50, "ceiling_height": 8, "complexity": "medium"}
            },
            "kitchen": {
                "materials": [
                    {"name": "Kitchen cabinets", "quantity": "12", "unit": "linear feet"},
                    {"name": "Countertop material", "quantity": "25", "unit": "sqft"},
                    {"name": "Backsplash tile", "quantity": "30", "unit": "sqft"},
                    {"name": "Cabinet hardware", "quantity": "20", "unit": "pieces"}
                ],
                "labor_hours": 48,
                "labor_breakdown": {"demo": 8, "installation": 32, "finishing": 8},
                "challenges": ["Plumbing and electrical coordination", "Appliance integration", "Level floor required"],
                "approach": "1. Demolition and preparation\n2. Cabinet installation with leveling\n3. Countertop templating and installation\n4. Backsplash tile work\n5. Hardware and finishing",
                "cost_factors": ["Cabinet quality", "Countertop material", "Appliance modifications"],
                "measurements": {"estimated_sqft": 120, "ceiling_height": 8, "complexity": "high"}
            },
            "general": {
                "materials": [
                    {"name": "Drywall", "quantity": "10", "unit": "sheets"},
                    {"name": "Joint compound", "quantity": "2", "unit": "buckets"},
                    {"name": "Paint", "quantity": "2", "unit": "gallons"},
                    {"name": "Primer", "quantity": "1", "unit": "gallon"}
                ],
                "labor_hours": 20,
                "labor_breakdown": {"demo": 4, "installation": 12, "finishing": 4},
                "challenges": ["Requires on-site verification", "Material quantity estimates approximate"],
                "approach": "1. Site assessment and measurements\n2. Surface preparation\n3. Installation of materials\n4. Finishing and cleanup",
                "cost_factors": ["Material quality", "Site accessibility", "Complexity of work"],
                "measurements": {"estimated_sqft": 100, "ceiling_height": 8, "complexity": "medium"}
            }
        }
        
        template = templates.get(project_type.lower(), templates["general"])
        template["model_used"] = "fallback"
        template["error"] = error
        template["note"] = "This is a template estimate. AI models were unavailable."
        
        return template
