import os

files = {
    "validation/schemas.py": """from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class HallucinationScore(BaseModel):
    is_hallucinated: bool
    fabricated_quotes: List[str] = Field(default_factory=list)
    unsupported_claims: List[str] = Field(default_factory=list)

class ContradictionReport(BaseModel):
    has_contradiction: bool
    conflicting_findings: List[Dict[str, Any]] = Field(default_factory=list)
    resolution_suggestion: str = ""

class ReliabilityMetrics(BaseModel):
    evidence_strength_score: float = Field(..., ge=0.0, le=1.0)
    theoretical_defensibility_score: float = Field(..., ge=0.0, le=1.0)
    statistical_support_score: float = Field(..., ge=0.0, le=1.0)
    hallucination_penalty: float = Field(default=0.0)
    overall_reliability_score: float = Field(..., ge=0.0, le=1.0)
    is_academically_defensible: bool

class ReviewerAnnotation(BaseModel):
    reviewer_id: str
    finding_id: str
    approved: bool
    comments: str
    override_interpretation: Optional[str] = None
""",

    "validation/hallucination.py": """from typing import List
from agents.schemas import AgentOutput, CorpusSegment
from validation.schemas import HallucinationScore
import re

class HallucinationDetector:
    \"\"\"Strictly verifies corpus grounding to prevent LLM hallucination.\"\"\"
    
    @staticmethod
    def verify_quotes(output: AgentOutput, segment: CorpusSegment) -> HallucinationScore:
        fabricated = []
        raw_text_normalized = " ".join(segment.raw_text.split())
        
        for finding in output.findings:
            for ev in finding.corpus_evidence:
                quote_normalized = " ".join(ev.exact_quote.split())
                if quote_normalized not in raw_text_normalized:
                    # Allow minor punctuation drift, but fail on word mismatch
                    clean_quote = re.sub(r'[^\\w\\s]', '', quote_normalized).strip()
                    clean_raw = re.sub(r'[^\\w\\s]', '', raw_text_normalized)
                    if clean_quote not in clean_raw:
                        fabricated.append(ev.exact_quote)
                        
        return HallucinationScore(
            is_hallucinated=len(fabricated) > 0,
            fabricated_quotes=fabricated
        )
""",

    "validation/contradiction.py": """from typing import List
from agents.schemas import AgentOutput
from validation.schemas import ContradictionReport
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

class ContradictionAnalyzer:
    \"\"\"Detects logical contradictions between multiple findings on the same segment.\"\"\"
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.0)
        
    async def analyze(self, output: AgentOutput) -> ContradictionReport:
        if len(output.findings) <= 1:
            return ContradictionReport(has_contradiction=False)
            
        # Fast fail logic: If ambiguity is explicitly declared, it's not a hidden contradiction
        ambiguities = [f for f in output.findings if f.ambiguity_level in ["Medium", "High"]]
        if len(ambiguities) == len(output.findings):
            return ContradictionReport(has_contradiction=False)
            
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a logical consistency checker. Analyze the following linguistic findings. Do they logically contradict each other without explicitly acknowledging the ambiguity? Return a JSON object with keys: has_contradiction (bool), conflicting_findings (list of finding types), resolution_suggestion (string)."),
            ("human", "{findings}")
        ])
        
        chain = prompt | self.llm.with_structured_output(ContradictionReport)
        return await chain.ainvoke({"findings": output.model_dump_json()})
""",

    "validation/reliability.py": """from agents.schemas import AgentOutput
from validation.schemas import ReliabilityMetrics, HallucinationScore

class ReliabilityScorer:
    \"\"\"Computes the final scientific reliability of an analysis.\"\"\"
    
    @staticmethod
    def calculate_score(output: AgentOutput, hallucination: HallucinationScore, has_stats: bool) -> ReliabilityMetrics:
        # Base scores
        evidence_strength = sum([len(f.corpus_evidence) for f in output.findings]) * 0.2
        evidence_strength = min(1.0, evidence_strength)
        
        theory_score = sum([f.confidence_score for f in output.findings]) / len(output.findings) if output.findings else 0.0
        
        stats_score = 1.0 if has_stats else 0.0
        halluc_penalty = 0.5 if hallucination.is_hallucinated else 0.0
        
        # Weighted Final
        overall = (evidence_strength * 0.4) + (theory_score * 0.4) + (stats_score * 0.2) - halluc_penalty
        overall = max(0.0, min(1.0, overall))
        
        return ReliabilityMetrics(
            evidence_strength_score=evidence_strength,
            theoretical_defensibility_score=theory_score,
            statistical_support_score=stats_score,
            hallucination_penalty=halluc_penalty,
            overall_reliability_score=overall,
            is_academically_defensible=overall >= 0.75
        )
""",

    "validation/self_correction.py": """from agents.schemas import AgentOutput, ValidationFeedback
from validation.schemas import ReliabilityMetrics

class SelfCorrectionEngine:
    \"\"\"Orchestrates the feedback loop when validation fails.\"\"\"
    
    @staticmethod
    def generate_feedback(output: AgentOutput, reliability: ReliabilityMetrics) -> ValidationFeedback:
        errors = []
        if not reliability.is_academically_defensible:
            errors.append(f"Reliability score {reliability.overall_reliability_score} is below academic threshold (0.75).")
            
        if reliability.hallucination_penalty > 0:
            errors.append("CRITICAL: Fabricated corpus evidence detected. Ensure all quotes match the raw text exactly.")
            
        if reliability.evidence_strength_score < 0.5:
            errors.append("Evidence strength is too low. Include more verbatim quotes.")
            
        return ValidationFeedback(
            is_valid=len(errors) == 0,
            errors=errors,
            suggested_correction=" | ".join(errors) if errors else None
        )
""",

    "validation/human_review.py": """from validation.schemas import ReviewerAnnotation

class HumanReviewWorkflow:
    \"\"\"Hooks for researcher dashboard manual overrides.\"\"\"
    
    def __init__(self):
        self.annotations = []
        
    def submit_review(self, annotation: ReviewerAnnotation):
        self.annotations.append(annotation)
        # TODO: Update Supabase report status
""",

    "tests/validation/test_hallucination.py": """import pytest
from validation.hallucination import HallucinationDetector
from agents.schemas import AgentOutput, CorpusSegment, LinguisticFinding, EvidenceReference

def test_hallucination_detector_pass():
    segment = CorpusSegment(segment_id="1", raw_text="The quick brown fox jumps.")
    finding = LinguisticFinding(
        finding_type="Test",
        linguistic_theory="Test Theory",
        interpretation="Test",
        theoretical_justification="Test",
        confidence_score=0.9,
        ambiguity_level="Low",
        corpus_evidence=[EvidenceReference(segment_id="1", exact_quote="quick brown fox")]
    )
    output = AgentOutput(findings=[finding], overall_confidence=0.9, reflection_log="")
    
    score = HallucinationDetector.verify_quotes(output, segment)
    assert not score.is_hallucinated

def test_hallucination_detector_fail():
    segment = CorpusSegment(segment_id="1", raw_text="The quick brown fox jumps.")
    finding = LinguisticFinding(
        finding_type="Test",
        linguistic_theory="Test Theory",
        interpretation="Test",
        theoretical_justification="Test",
        confidence_score=0.9,
        ambiguity_level="Low",
        corpus_evidence=[EvidenceReference(segment_id="1", exact_quote="lazy dog")]
    )
    output = AgentOutput(findings=[finding], overall_confidence=0.9, reflection_log="")
    
    score = HallucinationDetector.verify_quotes(output, segment)
    assert score.is_hallucinated
    assert "lazy dog" in score.fabricated_quotes
""",

    "tests/validation/test_reliability.py": """from validation.reliability import ReliabilityScorer
from validation.schemas import HallucinationScore
from agents.schemas import AgentOutput, LinguisticFinding, EvidenceReference

def test_reliability_scorer():
    finding = LinguisticFinding(
        finding_type="Test", linguistic_theory="Test Theory", interpretation="Test",
        theoretical_justification="Test", confidence_score=0.9, ambiguity_level="Low",
        corpus_evidence=[
            EvidenceReference(segment_id="1", exact_quote="A"),
            EvidenceReference(segment_id="1", exact_quote="B")
        ]
    )
    output = AgentOutput(findings=[finding], overall_confidence=0.9, reflection_log="")
    halluc = HallucinationScore(is_hallucinated=False)
    
    metrics = ReliabilityScorer.calculate_score(output, halluc, has_stats=True)
    assert metrics.is_academically_defensible
    assert metrics.overall_reliability_score > 0.7
"""
}

def scaffold_phase4():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    print("Phase 4 Validation & Reliability scaffolding complete.")

if __name__ == "__main__":
    scaffold_phase4()
