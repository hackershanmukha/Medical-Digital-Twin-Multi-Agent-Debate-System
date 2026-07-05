from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel

class DebateRequest(BaseModel):
    patient_id: str
    max_rounds: Optional[int] = 3

class AgentMessage(BaseModel):
    agent_name: str
    role: str
    round: int
    content: str

class DebateResponse(BaseModel):
    id: str
    patient_id: str
    predicted_risk: float
    risk_percentage: float
    explanation_attributions: dict[str, Any]
    transcript: List[AgentMessage]
    final_consensus_report: str
    created_at: datetime

    class Config:
        from_attributes = True
