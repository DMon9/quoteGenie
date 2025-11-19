from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime


class Material(BaseModel):
    name: str
    quantity: float
    unit: str
    unit_price: float
    total: float


class LaborItem(BaseModel):
    trade: str
    hours: float
    rate: float
    total: float


class Timeline(BaseModel):
    estimated_hours: float
    estimated_days: int
    min_days: int
    max_days: int


class WorkStep(BaseModel):
    order: int
    description: str
    duration: str


class Phase(BaseModel):
    name: str
    description: str
    estimated_hours: float


class RiskItem(BaseModel):
    id: str
    description: str
    impact: str  # low/medium/high


class QuoteResponse(BaseModel):
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
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}
