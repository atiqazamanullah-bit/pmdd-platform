from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class CorpusSegment(BaseModel):
    segment_id: str
    raw_text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class EvidenceReference(BaseModel):
    segment_id: str
    exact_quote: str
    char_start: Optional[int] = None
    char_end: Optional[int] = None

class LinguisticFinding(BaseModel):
    finding_type: str = Field(..., description="e.g., Speech Act, Implicature, Face-Threatening Act")
    linguistic_theory: str = Field(..., description="The theoretical framework applied.")
    interpretation: str = Field(..., description="The pragmatic or semantic interpretation.")
    theoretical_justification: str = Field(..., description="Why this theory applies to this segment.")
    corpus_evidence: List[EvidenceReference]
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    alternative_interpretation: Optional[str] = None
    ambiguity_level: str = Field(..., description="Low, Medium, or High")

class ValidationFeedback(BaseModel):
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    suggested_correction: Optional[str] = None

class AgentOutput(BaseModel):
    findings: List[LinguisticFinding]
    overall_confidence: float
    reflection_log: str = Field(..., description="Internal reasoning and self-correction narrative.")
    validation_status: str = "Pending"

class CognitiveState(BaseModel):
    session_id: str
    segment: CorpusSegment
    current_output: Optional[AgentOutput] = None
    validation_history: List[ValidationFeedback] = Field(default_factory=list)
    retry_count: int = 0
