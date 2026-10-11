from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class HealthResponse(BaseModel):
    status: str
    version: str


class TickerSummary(BaseModel):
    ticker: str
    price: float
    change_pct: float
    volume: float


class PredictionItem(BaseModel):
    date: str
    ticker: str
    close: float
    predicted_direction: str
    probability_up: float
    actual_direction: str


class SimilarStockItem(BaseModel):
    ticker: str
    similarity: float
