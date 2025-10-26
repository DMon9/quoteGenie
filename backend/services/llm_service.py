import os
import json
from typing import Dict, Any, List
import asyncio

class LLMService:
    """Handles LLM reasoning and text generation"""
    
    def __init__(self):
        # Provider selection: 'ollama' (default) or 'gemini'
        self.provider = os.getenv("LLM_PROVIDER", "ollama").lower()
        # Ollama config
        self.ollama_base_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3")
        # Gemini config
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.ready = False
        self._check_connection()
    
    def _check_connection(self):
        """Check if selected provider is available"""
        if self.provider == "gemini":
            if not self.google_api_key:
                print("Gemini selected but GOOGLE_API_KEY not set - falling back")
                self.ready = False
            else:
                # Assume ready if API key present; we'll handle errors on call
                self.ready = True
        else:
            try:
                import httpx
                response = httpx.get(f"{self.ollama_base_url}/api/tags", timeout=5.0)
                self.ready = response.status_code == 200
            except:
                print("Ollama not available - using fallback responses")
                self.ready = False
    
    def is_ready(self) -> bool:
        return self.ready
    
    async def reason_about_project(
        self,
        vision_results: Dict[str, Any],
        project_type: str,
        description: str = ""
    ) -> Dict[str, Any]:
        """Use LLM to reason about the project and generate recommendations"""
        
        prompt = self._build_reasoning_prompt(vision_results, project_type, description)
        
        if self.provider == "gemini" and self.google_api_key:
            response = await self._call_gemini(prompt)
        elif self.provider == "ollama" and self.ready:
            response = await self._call_ollama(prompt)
        else:
            response = self._fallback_response(project_type)
        
        return {
            "analysis": response,
            "recommendations": self._extract_recommendations(response),
            "materials_needed": self._extract_materials(response)
        }
    
    def _build_reasoning_prompt(self, vision_results: Dict, project_type: str, description: str) -> str:
        """Build structured prompt for LLM"""
        
        detections = vision_results.get("detections", [])
        measurements = vision_results.get("measurements", {})
        
        prompt = f"""You are an expert construction estimator analyzing a {project_type} project.

Vision Analysis Results:
- Detected objects: {[d['class'] for d in detections]}
- Estimated area: {measurements.get('estimated_area_sqft', 'unknown')} sq ft
- Scene: {vision_results.get('scene_description', 'unclear')}

{f'User description: {description}' if description else ''}

Based on this information:
1. List all materials needed with approximate quantities
2. Estimate labor hours required
3. Identify potential challenges or risks
4. Suggest the recommended approach

Respond in JSON format:
{{
  "materials": [
    {{"name": "material name", "quantity": "amount", "unit": "unit"}}
  ],
  "labor_hours": number,
  "challenges": ["challenge 1", "challenge 2"],
  "approach": "recommended approach description"
}}
"""
        return prompt
    
    async def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API"""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    return response.json().get("response", "")
                else:
                    return self._fallback_response()
        except Exception as e:
            print(f"Ollama API error: {e}")
            return self._fallback_response()

    async def _call_gemini(self, prompt: str) -> str:
        """Call Google Gemini API (run sync client in a worker thread)."""
        try:
            def run_sync_call() -> str:
                import google.generativeai as genai
                genai.configure(api_key=self.google_api_key)
                model = genai.GenerativeModel(self.gemini_model)
                resp = model.generate_content(prompt)
                return getattr(resp, "text", str(resp))

            return await asyncio.to_thread(run_sync_call)
        except Exception as e:
            print(f"Gemini API error: {e}")
            return self._fallback_response()
    
    def _fallback_response(self, project_type: str = "general") -> str:
        """Fallback when LLM is unavailable"""
        
        templates = {
            "bathroom": {
                "materials": [
                    {"name": "tile", "quantity": "50", "unit": "sqft"},
                    {"name": "grout", "quantity": "2", "unit": "bags"},
                    {"name": "adhesive", "quantity": "1", "unit": "bucket"}
                ],
                "labor_hours": 20,
                "challenges": ["Requires plumbing work", "Waterproofing critical"],
                "approach": "Remove old fixtures, install waterproofing, tile work, fixture installation"
            },
            "kitchen": {
                "materials": [
                    {"name": "cabinets", "quantity": "12", "unit": "linear feet"},
                    {"name": "countertop", "quantity": "25", "unit": "sqft"},
                    {"name": "backsplash tile", "quantity": "30", "unit": "sqft"}
                ],
                "labor_hours": 40,
                "challenges": ["Plumbing and electrical coordination", "Appliance integration"],
                "approach": "Demo, cabinet installation, countertop templating and install, backsplash"
            },
            "general": {
                "materials": [
                    {"name": "drywall", "quantity": "10", "unit": "sheets"},
                    {"name": "joint compound", "quantity": "2", "unit": "buckets"},
                    {"name": "paint", "quantity": "2", "unit": "gallons"}
                ],
                "labor_hours": 16,
                "challenges": ["Requires measurement verification"],
                "approach": "Standard renovation approach with proper preparation"
            }
        }
        
        template = templates.get(project_type.lower(), templates["general"])
        return json.dumps(template)
    
    def _extract_recommendations(self, response: str) -> List[str]:
        """Extract recommendations from LLM response"""
        try:
            # Clean markdown code blocks if present
            cleaned = response.strip()
            if "```json" in cleaned or "```" in cleaned:
                # Remove markdown fences
                cleaned = cleaned.replace("```json", "").replace("```", "").strip()
            
            data = json.loads(cleaned)
            return data.get("challenges", [])
        except Exception as e:
            print(f"Failed to extract recommendations: {e}")
            return ["Verify measurements on-site", "Check local building codes"]
    
    def _extract_materials(self, response: str) -> List[Dict]:
        """Extract materials list from LLM response"""
        try:
            # Clean markdown code blocks if present
            cleaned = response.strip()
            if "```json" in cleaned or "```" in cleaned:
                # Remove markdown fences
                cleaned = cleaned.replace("```json", "").replace("```", "").strip()
            
            print(f"DEBUG: Parsing materials from cleaned JSON ({len(cleaned)} chars)")
            data = json.loads(cleaned)
            materials = data.get("materials", [])
            print(f"DEBUG: Found {len(materials)} materials in JSON")
            return materials
        except Exception as e:
            print(f"Failed to extract materials: {e}")
            import traceback
            traceback.print_exc()
            return []
