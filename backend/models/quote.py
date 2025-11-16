from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class Material:
    name: str
    quantity: float
    unit: str
    unit_price: float
    total: float

@dataclass
class LaborItem:
    trade: str
    hours: float
    rate: float
    total: float

@dataclass
class Timeline:
    estimated_hours: float
    estimated_days: int
    min_days: int
    max_days: int

@dataclass
class WorkStep:
    order: int
    description: str
    duration: str


@dataclass
class Phase:
    name: str
    description: str
    estimated_hours: float


@dataclass
class RiskItem:
    id: str
    description: str
    impact: str  # low/medium/high

@dataclass
class QuoteResponse:
    id: str
    status: str
    total_cost: Dict[str, Any]
    timeline: Timeline
    materials: List[Material]
    labor: List[LaborItem]
    steps: List[WorkStep]
    confidence_score: float
    vision_analysis: Optional[Dict[str, Any]] = None
    options_applied: Optional[Dict[str, Any]] = None
    scope: Optional[str] = None
    phases: Optional[List[Phase]] = None
    risks: Optional[List[RiskItem]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Lightweight serializer: ensure datetime is ISO 8601 when converting to dict
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        if isinstance(self.created_at, datetime):
            result["created_at"] = self.created_at.isoformat()
        return result
