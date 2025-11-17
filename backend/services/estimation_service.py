import json
import time
import re
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
import os
import json as _json
import csv
from services.pricing_service import PricingService


class EstimationService:
    """Handles cost estimation and pricing logic"""

    def __init__(self):
        self.materials_db = self._load_materials_db()
        self.labor_rates = self._load_labor_rates()

        # Optional external pricing backend (watsonx.data)
        self.pricing: Optional[PricingService] = None
        try:
            self.pricing = PricingService()
        except Exception:
            self.pricing = None

        # External price list hot-reload tracking
        self._external_price_files: List[Path] = []
        self._external_price_mtimes: Dict[str, float] = {}
        self._external_keys: Set[str] = set()
        self._price_list_reload_interval = float(os.getenv("PRICE_LIST_RELOAD_SEC", "10"))
        self._price_list_last_check = 0.0
        self._load_external_price_lists()

    def _load_materials_db(self) -> Dict:
        """Load material prices database"""
        return {
            # General materials
            "drywall": {"price": 12.50, "unit": "sheet", "description": "4x8 drywall sheet"},
            "joint_compound": {"price": 15.00, "unit": "bucket", "description": "Joint compound 5-gal"},
            "paint": {"price": 35.00, "unit": "gallon", "description": "Interior paint"},
            "primer": {"price": 25.00, "unit": "gallon", "description": "Paint primer"},
            "lumber_2x4": {"price": 5.50, "unit": "piece", "description": "2x4x8 lumber"},
            "lumber_2x4_treated": {"price": 6.50, "unit": "piece", "description": "2x4x8 treated lumber"},
            "tile": {"price": 3.50, "unit": "sqft", "description": "Ceramic tile"},
            "grout": {"price": 20.00, "unit": "bag", "description": "Tile grout"},
            "grout_sealer": {"price": 18.00, "unit": "quart", "description": "Grout sealer"},
            "adhesive": {"price": 25.00, "unit": "bucket", "description": "Tile adhesive / thinset"},
            "thin_set_mortar": {"price": 18.00, "unit": "bag", "description": "Thin-set mortar 50lb"},
            "cement_backer_board": {"price": 14.00, "unit": "sheet", "description": "3'x5' cement backer board"},
            "concrete_3000psi": {"price": 135.00, "unit": "cubic_yard", "description": "Ready-mix concrete 3000 PSI"},
            # Kitchen
            "cabinets": {"price": 150.00, "unit": "linear_foot", "description": "Stock cabinets"},
            "countertop": {"price": 45.00, "unit": "sqft", "description": "Laminate countertop"},
            "backsplash": {"price": 8.00, "unit": "sqft", "description": "Backsplash tile"},
        }

    def _load_labor_rates(self) -> Dict:
        """Load labor rates by trade"""
        return {
            "general": {"rate": 45.00, "unit": "hour"},
            "drywall": {"rate": 50.00, "unit": "hour"},
            "painting": {"rate": 40.00, "unit": "hour"},
            "plumbing": {"rate": 75.00, "unit": "hour"},
            "electrical": {"rate": 80.00, "unit": "hour"},
            "tile": {"rate": 55.00, "unit": "hour"},
            "carpentry": {"rate": 60.00, "unit": "hour"},
        }

    def _load_external_price_lists(self) -> None:
        """Load one or more alternate pricing lists from file(s) to override defaults.

        Env vars:
        - PRICE_LIST_FILE or PRICING_FILE: single file path
        - PRICE_LIST_FILES or PRICING_FILES: comma-separated file paths
        Supports JSON dict or list, and CSV/TSV with key,price,unit,description
        """
        paths: List[str] = []
        single = os.getenv("PRICE_LIST_FILE") or os.getenv("PRICING_FILE")
        multi = os.getenv("PRICE_LIST_FILES") or os.getenv("PRICING_FILES")
        if single:
            paths.append(single)
        if multi:
            for p in multi.split(","):
                p = p.strip()
                if p:
                    paths.append(p)

        # Normalize paths
        file_paths: List[Path] = []
        for p in paths:
            try:
                path = Path(p)
                if not path.is_absolute():
                    path = Path.cwd() / path
                file_paths.append(path)
            except Exception:
                continue

        # Clear existing external overrides to handle deletions
        for k in list(self._external_keys):
            if k in self.materials_db:
                del self.materials_db[k]
        self._external_keys.clear()
        self._external_price_files = []

        for path in file_paths:
            try:
                if not path.exists():
                    continue
                if path.suffix.lower() == ".json":
                    with open(path, "r", encoding="utf-8") as f:
                        data = _json.load(f)
                    if isinstance(data, dict):
                        for key, rec in data.items():
                            if not isinstance(rec, dict):
                                continue
                            price = rec.get("price")
                            if price is None:
                                continue
                            unit = rec.get("unit", "unit")
                            desc = rec.get("description", self.materials_db.get(key, {}).get("description"))
                            self.materials_db[key] = {
                                "price": float(price),
                                "unit": unit,
                                "description": desc or key.replace("_", " "),
                            }
                            self._external_keys.add(key)
                    elif isinstance(data, list):
                        loaded_count = 0
                        sample_keys: List[str] = []
                        for rec in data:
                            if not isinstance(rec, dict):
                                continue
                            # Case-insensitive field extraction helpers
                            def _ci(rec: Dict[str, Any], *names: str) -> Optional[Any]:
                                for n in names:
                                    if n in rec:
                                        return rec[n]
                                # try lowercase fallback
                                lower = {k.lower(): v for k, v in rec.items()}
                                for n in names:
                                    v = lower.get(n.lower())
                                    if v is not None:
                                        return v
                                return None

                            price = _ci(rec, "price", "Final_Price_USD", "Base_Cost_USD")
                            if price is None:
                                continue
                            key_raw = _ci(rec, "key")
                            key = key_raw.strip() if isinstance(key_raw, str) else ""
                            name_val = _ci(rec, "name", "material", "title", "Material")
                            name = name_val.strip() if isinstance(name_val, str) else ""
                            if not key:
                                key = self._name_to_db_key(name) if name else ""
                            if not key:
                                continue
                            unit_val = _ci(rec, "unit", "Unit_Type")
                            unit = unit_val if isinstance(unit_val, str) and unit_val.strip() else self.materials_db.get(key, {}).get("unit", "unit")
                            desc_val = _ci(rec, "description", "Description", "Category")
                            desc = (
                                desc_val if isinstance(desc_val, str) and desc_val.strip() else self.materials_db.get(key, {}).get("description") or (name or key.replace("_", " "))
                            )
                            try:
                                self.materials_db[key] = {
                                    "price": float(price),
                                    "unit": unit,
                                    "description": desc,
                                }
                                self._external_keys.add(key)
                                loaded_count += 1
                                if len(sample_keys) < 5:
                                    sample_keys.append(key)
                            except Exception:
                                continue
                        try:
                            print(f"Price list loaded from {path}: {loaded_count} entries (e.g., {', '.join(sample_keys)})")
                        except Exception:
                            pass
                elif path.suffix.lower() in (".csv", ".tsv"):
                    delim = "," if path.suffix.lower() == ".csv" else "\t"
                    with open(path, "r", encoding="utf-8") as f:
                        reader = csv.DictReader(f, delimiter=delim)
                        for row in reader:
                            key = (row.get("key") or "").strip()
                            if not key:
                                continue
                            price_field = row.get("price")
                            if price_field is None or str(price_field).strip() == "":
                                continue
                            try:
                                price = float(str(price_field).strip())
                            except Exception:
                                continue
                            unit = (row.get("unit") or "unit").strip()
                            desc = (row.get("description") or self.materials_db.get(key, {}).get("description") or key.replace("_", " ")).strip()
                            self.materials_db[key] = {"price": price, "unit": unit, "description": desc}
                            self._external_keys.add(key)
                else:
                    # Unknown extension, try JSON parse
                    with open(path, "r", encoding="utf-8") as f:
                        data = _json.load(f)
                    if isinstance(data, dict):
                        for key, rec in data.items():
                            if not isinstance(rec, dict) or rec.get("price") is None:
                                continue
                            self.materials_db[key] = {
                                "price": float(rec["price"]),
                                "unit": rec.get("unit", "unit"),
                                "description": rec.get("description", key.replace("_", " ")),
                            }
                            self._external_keys.add(key)

                # Track for hot reload
                self._external_price_files.append(path)
                try:
                    self._external_price_mtimes[str(path)] = path.stat().st_mtime
                except Exception:
                    self._external_price_mtimes[str(path)] = 0.0
            except Exception as e:
                print(f"Price list load failed for {path}: {e}")

        self._price_list_last_check = time.time()

    def _maybe_reload_price_lists(self) -> None:
        if not self._external_price_files:
            return
        now = time.time()
        if now - self._price_list_last_check < self._price_list_reload_interval:
            return
        changed = False
        for path in self._external_price_files:
            try:
                mtime = path.stat().st_mtime
                if mtime > self._external_price_mtimes.get(str(path), 0.0):
                    changed = True
                    break
            except Exception:
                changed = True
                break
        if changed:
            self._load_external_price_lists()

    async def calculate_estimate(
        self,
        vision_results: Dict,
        reasoning: Dict,
        project_type: str,
        advanced_options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Calculate complete project estimate with optional advanced options
        
        Args:
            vision_results: Vision analysis results
            reasoning: LLM reasoning output
            project_type: Type of project (bathroom, kitchen, etc.)
            advanced_options: Optional dict with:
                - quality: "standard", "premium", "luxury" (affects material multiplier)
                - contingency_pct: float (default 0, range 0-30)
                - profit_pct: float (default 15, range 0-50)
                - region: "midwest", "south", "northeast", "west" (affects labor rates)
        """

        # Hot-reload pricing lists if files changed
        self._maybe_reload_price_lists()
        
        # Parse advanced options with defaults
        opts = advanced_options or {}
        material_quality = opts.get("quality", "standard")
        # Auto-upgrade quality based on vision description if not explicitly provided
        try:
            if ("quality" not in opts) and isinstance(vision_results.get("scene_description"), str):
                if "luxury" in vision_results["scene_description"].lower():
                    material_quality = "luxury"
        except Exception:
            pass
        contingency_pct = self._parse_float(opts.get("contingency_pct"), default=0.0, min_val=0.0, max_val=30.0)
        profit_pct = self._parse_float(opts.get("profit_pct"), default=15.0, min_val=0.0, max_val=50.0)
        region = opts.get("region", "midwest")

        # Extract materials from LLM reasoning
        materials_needed = reasoning.get("materials_needed", [])

        # Scale quantities and labor by estimated area when available to better reflect project size
        area_factor = 1.0
        try:
            est_area = float(vision_results.get("measurements", {}).get("estimated_area_sqft") or 0)
            # Baseline areas by project type (heuristic) - updated for more accurate ratios
            baselines = {"bathroom": 60.0, "kitchen": 100.0, "interior": 800.0, "exterior": 200.0}
            baseline = baselines.get(project_type.lower(), 100.0)
            if est_area > 0 and baseline > 0:
                # Use square root scaling to dampen extreme variations
                raw_ratio = est_area / baseline
                area_factor = max(0.6, min(3.0, raw_ratio ** 0.7))
        except Exception:
            area_factor = 1.0

        if area_factor != 1.0 and isinstance(materials_needed, list):
            scaled: List[Dict[str, Any]] = []
            for m in materials_needed:
                try:
                    q = m.get("quantity", 0)
                    # _parse_quantity will be applied later; here just scale numeric values
                    if isinstance(q, (int, float)):
                        q = float(q) * area_factor
                    scaled.append({**m, "quantity": q})
                except Exception:
                    scaled.append(m)
            materials_needed = scaled

        # Calculate material costs with quality multiplier
        materials_cost = self._calculate_materials_cost(materials_needed, quality=material_quality)

        # Calculate labor costs with region multiplier
        labor_hours = self._extract_labor_hours(reasoning) * area_factor
        labor_cost = self._calculate_labor_cost(labor_hours, project_type, region=region)

        # Apply subtype multipliers for specific exterior cases (e.g., roof replacement is materially costlier)
        subtype_multiplier = 1.0
        try:
            if project_type.lower() == "exterior":
                desc = str(vision_results.get("scene_description", "")).lower()
                detections = vision_results.get("detections", []) or []
                has_roof = ("roof" in desc) or any("roof" in str(d.get("class", "")).lower() for d in detections)
                if has_roof:
                    subtype_multiplier = 1.6
        except Exception:
            pass

        # Apply profit margin and contingency
        subtotal = (materials_cost["total"] + labor_cost["total"]) * subtype_multiplier
        profit = subtotal * (profit_pct / 100.0)
        contingency = subtotal * (contingency_pct / 100.0)
        total = subtotal + profit + contingency

        # Estimate timeline
        timeline = self._estimate_timeline(labor_hours)

        # Generate step-by-step plan
        steps = self._generate_work_steps(project_type, materials_needed)

        return {
            "total_cost": {
                "currency": "USD",
                "amount": round(total, 2),
                "breakdown": {
                    "materials": round(materials_cost["total"], 2),
                    "labor": round(labor_cost["total"], 2),
                    "profit": round(profit, 2),
                    "contingency": round(contingency, 2),
                },
            },
            "materials": materials_cost["items"],
            "labor": labor_cost["items"],
            "timeline": timeline,
            "steps": steps,
            "confidence_score": self._calculate_confidence(vision_results),
            "options_applied": {
                "quality": material_quality,
                "contingency_pct": contingency_pct,
                "profit_pct": profit_pct,
                "region": region,
            },
        }

    def _parse_float(self, value: Any, default: float = 0.0, min_val: Optional[float] = None, max_val: Optional[float] = None) -> float:
        """Parse and clamp a float value"""
        try:
            result = float(value) if value is not None else default
            if min_val is not None:
                result = max(min_val, result)
            if max_val is not None:
                result = min(max_val, result)
            return result
        except (ValueError, TypeError):
            return default

    def _extract_labor_hours(self, reasoning: Dict) -> float:
        """Extract labor hours from reasoning"""
        try:
            analysis = reasoning.get("analysis", "{}")
            if isinstance(analysis, str):
                data = json.loads(analysis)
            else:
                data = analysis
            return float(data.get("labor_hours", 16))
        except Exception:
            return 16.0

    def _calculate_materials_cost(self, materials: List[Dict], quality: str = "standard") -> Dict:
        """Calculate total material costs with quality multiplier
        
        Args:
            materials: List of material dicts
            quality: "standard" (1.0x), "premium" (1.3x), "luxury" (1.8x)
        """
        quality_multipliers = {
            "standard": 1.0,
            "premium": 1.3,
            "luxury": 1.8,
        }
        multiplier = quality_multipliers.get(quality.lower(), 1.0)
        
        items: List[Dict[str, Any]] = []
        total = 0.0

        for material in materials:
            raw_name = str(material.get("name", "")).strip()
            db_key = self._name_to_db_key(raw_name)

            # Parse quantity (can be number or string like "3 50lb bags")
            quantity_val = material.get("quantity", 0)
            quantity = self._parse_quantity(quantity_val)

            # Prefer external pricing if available
            price_data = None
            if self.pricing is not None:
                try:
                    rec = self.pricing.get_price(db_key)
                    if rec and rec.get("price") is not None:
                        price_data = {"price": float(rec["price"]), "unit": rec.get("unit") or "unit"}
                except Exception:
                    price_data = None
            # Fallback to local DB
            if price_data is None:
                price_data = self.materials_db.get(db_key, {"price": 10.0, "unit": "unit"})
            unit_price = float(price_data.get("price", 10.0)) * multiplier
            line_total = float(quantity) * unit_price

            items.append(
                {
                    "name": raw_name or db_key.replace("_", " "),
                    "quantity": quantity,
                    "unit": material.get("unit") or price_data.get("unit") or "unit",
                    "unit_price": round(unit_price, 2),
                    "total": round(line_total, 2),
                }
            )

            total += line_total

        return {"items": items, "total": total}

    def _parse_quantity(self, value: Any) -> float:
        """Parse quantity which may be numeric or a string like '3 50lb bags'."""
        try:
            if isinstance(value, (int, float)):
                return float(value)
            s = str(value).strip()
            m = re.match(r"\s*([0-9]*\.?[0-9]+)", s)
            if m:
                return float(m.group(1))
            return 0.0
        except Exception:
            return 0.0

    def _name_to_db_key(self, name: str) -> str:
        """Map common material names to database keys."""
        n = name.lower().strip()
        mapping = {
            "floor & wall tile": "tile",
            "floor and wall tile": "tile",
            "tile": "tile",
            "unsanded grout": "grout",
            "grout": "grout",
            "grout sealer": "grout_sealer",
            "thin-set mortar": "thin_set_mortar",
            "thin set mortar": "thin_set_mortar",
            "thinset": "thin_set_mortar",
            "tile adhesive": "adhesive",
            "adhesive": "adhesive",
            "cement backer board": "cement_backer_board",
            "backer board": "cement_backer_board",
            "cement board": "cement_backer_board",
            "lumber (2x4x8 treated)": "lumber_2x4_treated",
            "lumber (2x4x8 untreated)": "lumber_2x4",
            "2x4": "lumber_2x4",
            "concrete (3000 psi)": "concrete_3000psi",
            "concrete": "concrete_3000psi",
            "drywall": "drywall",
            "joint compound": "joint_compound",
            "paint": "paint",
            "primer": "primer",
            "backsplash tile": "backsplash",
            "countertop": "countertop",
            "cabinets": "cabinets",
        }
        if n in mapping:
            return mapping[n]
        if "tile" in n and "backer" not in n:
            return "tile"
        if "grout" in n and "sealer" not in n:
            return "grout"
        if "sealer" in n and "grout" in n:
            return "grout_sealer"
        if "backer" in n or "cement board" in n:
            return "cement_backer_board"
        if "thin" in n and "mortar" in n:
            return "thin_set_mortar"
        if "2x4" in n:
            return "lumber_2x4"
        if "concrete" in n:
            return "concrete_3000psi"
        return n.replace(" ", "_")

    def _calculate_labor_cost(self, hours: float, project_type: str, region: str = "midwest") -> Dict:
        """Calculate labor costs with regional adjustment
        
        Args:
            hours: Labor hours
            project_type: Project type
            region: "midwest" (1.0x), "south" (0.85x), "northeast" (1.25x), "west" (1.35x)
        """
        region_multipliers = {
            "midwest": 1.0,
            "south": 0.85,
            "northeast": 1.25,
            "west": 1.35,
        }
        multiplier = region_multipliers.get(region.lower(), 1.0)
        
        trade = self._map_project_to_trade(project_type)
        rate_info = self.labor_rates.get(trade, self.labor_rates["general"])
        base_rate = rate_info["rate"]
        hourly_rate = base_rate * multiplier
        total = hours * hourly_rate
        return {
            "items": [
                {
                    "trade": trade,
                    "hours": hours,
                    "rate": round(hourly_rate, 2),
                    "base_rate": base_rate,
                    "region_multiplier": multiplier,
                    "total": round(total, 2)
                }
            ],
            "total": total,
        }

    def _map_project_to_trade(self, project_type: str) -> str:
        mapping = {
            "bathroom": "tile",
            "kitchen": "carpentry",
            "electrical": "electrical",
            "painting": "painting",
            "drywall": "drywall",
            "plumbing": "plumbing",
        }
        return mapping.get(project_type.lower(), "general")

    def _estimate_timeline(self, hours: float) -> Dict:
        days = max(1, round(hours / 8))
        return {
            "estimated_hours": hours,
            "estimated_days": days,
            "min_days": max(1, days - 1),
            "max_days": days + 2,
        }

    def _generate_work_steps(self, project_type: str, materials: List[Dict]) -> List[Dict]:
        templates = {
            "bathroom": [
                {"order": 1, "description": "Remove old fixtures and materials", "duration": "4 hours"},
                {"order": 2, "description": "Install waterproofing membrane", "duration": "3 hours"},
                {"order": 3, "description": "Tile installation", "duration": "8 hours"},
                {"order": 4, "description": "Grout and seal", "duration": "4 hours"},
                {"order": 5, "description": "Install new fixtures", "duration": "4 hours"},
            ],
            "kitchen": [
                {"order": 1, "description": "Demo existing cabinets and countertops", "duration": "6 hours"},
                {"order": 2, "description": "Wall preparation and repairs", "duration": "4 hours"},
                {"order": 3, "description": "Install base and wall cabinets", "duration": "12 hours"},
                {"order": 4, "description": "Template and install countertops", "duration": "8 hours"},
                {"order": 5, "description": "Install backsplash", "duration": "6 hours"},
            ],
            "general": [
                {"order": 1, "description": "Site preparation and protection", "duration": "2 hours"},
                {"order": 2, "description": "Demolition (if required)", "duration": "4 hours"},
                {"order": 3, "description": "Framing and structural work", "duration": "8 hours"},
                {"order": 4, "description": "Installation of materials", "duration": "12 hours"},
                {"order": 5, "description": "Finishing and cleanup", "duration": "4 hours"},
            ],
        }
        return templates.get(project_type.lower(), templates["general"])

    def _calculate_confidence(self, vision_results: Dict) -> float:
        detections = vision_results.get("detections", [])
        if not detections:
            return 0.5
        avg_confidence = sum(d.get("confidence", 0) for d in detections) / len(detections)
        return round(min(avg_confidence * 0.9, 0.85), 2)

    async def search_materials(self, query: str, limit: int = 10) -> List[Dict]:
        results = []
        query_lower = query.lower()
        for name, data in self.materials_db.items():
            if query_lower in name or query_lower in data.get("description", "").lower():
                results.append(
                    {
                        "name": name,
                        "price": data["price"],
                        "unit": data["unit"],
                        "description": data["description"],
                    }
                )
        return results[:limit]

    async def get_labor_rates(self, trade: Optional[str] = None) -> Dict:
        if trade:
            return {trade: self.labor_rates.get(trade)}
        return self.labor_rates

    # --- Utilities for ops/endpoints ---
    def reload_price_lists(self) -> Dict[str, Any]:
        """Force reload of external price lists and return a summary."""
        self._load_external_price_lists()
        return {
            "files": [str(p) for p in self._external_price_files],
            "keys_loaded": len(self._external_keys),
            "last_check": self._price_list_last_check,
            "interval_sec": self._price_list_reload_interval,
        }

    def lookup_price(self, key_or_name: str) -> Dict[str, Any]:
        """Lookup price for a given key or raw name using all layers (pricing service -> local DB)."""
        key = self._name_to_db_key(key_or_name)
        # Try external pricing service first
        if self.pricing is not None:
            try:
                rec = self.pricing.get_price(key)
                if rec and rec.get("price") is not None:
                    return {"key": key, "source": "external", "price": float(rec["price"]), "unit": rec.get("unit") or "unit"}
            except Exception:
                pass
        # Fallback to local DB
        rec = self.materials_db.get(key)
        if rec:
            src = "external-list" if key in self._external_keys else "local"
            return {"key": key, "source": src, "price": float(rec.get("price", 0.0)), "unit": rec.get("unit", "unit")}
        return {"key": key, "source": "none"}
