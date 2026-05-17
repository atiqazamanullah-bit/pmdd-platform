import os

files = {
    "agents/schemas.py": """from pydantic import BaseModel, Field
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
""",

    "agents/base.py": """from abc import ABC, abstractmethod
from typing import Any, Dict
from agents.schemas import CognitiveState, AgentOutput, ValidationFeedback
import logging

logger = logging.getLogger("pmdd.agents")

class BaseCognitiveAgent(ABC):
    def __init__(self, agent_name: str, max_retries: int = 3):
        self.agent_name = agent_name
        self.max_retries = max_retries

    async def execute(self, state: CognitiveState) -> AgentOutput:
        \"\"\"The main cognitive loop.\"\"\"
        logger.info(f"[{self.agent_name}] Starting cognitive cycle for segment {state.segment.segment_id}")
        
        # 1. Observe (Load Context & Memory)
        context = await self.observe(state)
        
        while state.retry_count < self.max_retries:
            # 2. Analyze
            if state.retry_count == 0:
                output = await self.analyze(context, state)
            else:
                # 4 & 5. Reflect and Correct
                output = await self.reflect_and_correct(context, state)
            
            state.current_output = output
            
            # 3. Validate
            validation = await self.validate(output, state)
            state.validation_history.append(validation)
            
            if validation.is_valid:
                # 6 & 7. Score & Store
                output.validation_status = "Passed"
                await self.store_memory(state, success=True)
                return output
            
            logger.warning(f"[{self.agent_name}] Validation failed: {validation.errors}. Retrying...")
            state.retry_count += 1

        # Fallback if max retries reached
        logger.error(f"[{self.agent_name}] Max retries reached.")
        if state.current_output:
            state.current_output.validation_status = "Failed"
        await self.store_memory(state, success=False)
        return state.current_output

    @abstractmethod
    async def observe(self, state: CognitiveState) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def analyze(self, context: Dict[str, Any], state: CognitiveState) -> AgentOutput:
        pass

    @abstractmethod
    async def validate(self, output: AgentOutput, state: CognitiveState) -> ValidationFeedback:
        pass

    @abstractmethod
    async def reflect_and_correct(self, context: Dict[str, Any], state: CognitiveState) -> AgentOutput:
        pass

    @abstractmethod
    async def store_memory(self, state: CognitiveState, success: bool):
        pass
""",

    "agents/agent1_preprocessor.py": """import uuid
import logging
from typing import List, Dict, Any
from agents.schemas import CorpusSegment

logger = logging.getLogger("pmdd.agent1")

class CorpusPreprocessor:
    \"\"\"Agent 1: Handles ingestion, normalization, and chunking.\"\"\"
    
    def __init__(self):
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm", disable=["ner", "parser", "tagger", "lemmatizer"])
            self.nlp.add_pipe("sentencizer")
        except ImportError:
            logger.warning("Spacy not found. Using naive splitting.")
            self.nlp = None
        except OSError:
            logger.warning("Spacy model 'en_core_web_sm' not found. Please run: python -m spacy download en_core_web_sm")
            self.nlp = None

    async def ingest_file(self, file_content: str, metadata: Dict[str, Any]) -> List[CorpusSegment]:
        \"\"\"Validates and chunks raw text into manageable segments.\"\"\"
        if not file_content or not file_content.strip():
            raise ValueError("Corrupted or empty file content.")
            
        cleaned_text = self._normalize(file_content)
        chunks = self._chunk_text(cleaned_text)
        
        segments = []
        for i, chunk in enumerate(chunks):
            seg_meta = metadata.copy()
            seg_meta["chunk_index"] = i
            segments.append(
                CorpusSegment(
                    segment_id=str(uuid.uuid4()),
                    raw_text=chunk,
                    metadata=seg_meta
                )
            )
        return segments

    def _normalize(self, text: str) -> str:
        # Remove null bytes, fix encoding issues, collapse excessive whitespace
        text = text.replace("\\x00", "")
        return " ".join(text.split())

    def _chunk_text(self, text: str, max_words: int = 500) -> List[str]:
        if self.nlp:
            doc = self.nlp(text)
            sentences = [sent.text for sent in doc.sents]
        else:
            sentences = text.split(". ")
            
        chunks = []
        current_chunk = []
        current_len = 0
        
        for sent in sentences:
            words = len(sent.split())
            if current_len + words > max_words and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sent]
                current_len = words
            else:
                current_chunk.append(sent)
                current_len += words
                
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks
""",

    "agents/agent2_pragmatic.py": """from typing import Dict, Any
import os
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from agents.base import BaseCognitiveAgent
from agents.schemas import CognitiveState, AgentOutput, ValidationFeedback
from agents.prompts import PRAGMATIC_SYSTEM_PROMPT

class PragmaticAnalyzerAgent(BaseCognitiveAgent):
    \"\"\"Agent 2: Advanced Pragmatic Reasoning.\"\"\"
    
    def __init__(self):
        super().__init__(agent_name="Agent2_Pragmatic", max_retries=3)
        # We rely on OPENAI_API_KEY being set in env
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
        self.structured_llm = self.llm.with_structured_output(AgentOutput)

    async def observe(self, state: CognitiveState) -> Dict[str, Any]:
        # TODO: Fetch episodic memory
        memory_context = "No specific episodic memory found for this pattern."
        return {"memory": memory_context}

    async def analyze(self, context: Dict[str, Any], state: CognitiveState) -> AgentOutput:
        prompt = ChatPromptTemplate.from_messages([
            ("system", PRAGMATIC_SYSTEM_PROMPT),
            ("human", "Memory Context: {memory}\\n\\nAnalyze the following segment:\\n{text}")
        ])
        
        chain = prompt | self.structured_llm
        result = await chain.ainvoke({
            "memory": context["memory"],
            "text": state.segment.raw_text
        })
        return result

    async def validate(self, output: AgentOutput, state: CognitiveState) -> ValidationFeedback:
        errors = []
        if output.overall_confidence < 0.7:
            errors.append("Overall confidence is too low.")
        for finding in output.findings:
            for ev in finding.corpus_evidence:
                if ev.exact_quote not in state.segment.raw_text:
                    errors.append(f"Hallucination detected: Quote '{ev.exact_quote}' not found in source text.")
                    
        return ValidationFeedback(
            is_valid=len(errors) == 0,
            errors=errors,
            suggested_correction="Ensure all quotes exactly match the provided segment text and increase theoretical rigor." if errors else None
        )

    async def reflect_and_correct(self, context: Dict[str, Any], state: CognitiveState) -> AgentOutput:
        last_feedback = state.validation_history[-1]
        prompt = ChatPromptTemplate.from_messages([
            ("system", PRAGMATIC_SYSTEM_PROMPT),
            ("human", "Analyze this segment: {text}\\n\\nYOUR PREVIOUS ATTEMPT FAILED. Feedback: {feedback}\\nCorrect your analysis and ensure perfect evidence tracing.")
        ])
        chain = prompt | self.structured_llm
        return await chain.ainvoke({
            "text": state.segment.raw_text,
            "feedback": last_feedback.errors
        })

    async def store_memory(self, state: CognitiveState, success: bool):
        # Stub for Pinecone integration
        pass
""",

    "agents/prompts.py": """PRAGMATIC_SYSTEM_PROMPT = \"\"\"You are Agent 2 (Pragmatic Analyzer), a post-doctoral computational linguist expert.
Your task is to perform a rigorous pragmatic analysis of the provided text segment.

You must dynamically apply relevant linguistic theories, including:
- Speech Act Theory (Searle, Austin)
- Gricean Maxims and Conversational Implicature
- Politeness Theory and Face-Threatening Acts (Brown & Levinson)
- Relevance Theory

Requirements:
1. Identify pragmatic drift, indirectness, or implicature.
2. Ground EVERY finding with an exact verbatim quote from the text.
3. If the text is ambiguous, state the ambiguity and provide alternative interpretations.
4. Provide a confidence score (0.0 to 1.0).
5. Explain your internal reasoning in the 'reflection_log'.

DO NOT hallucinate quotes. The 'exact_quote' field MUST be a substring of the provided text.
\"\"\"
""",

    "tests/agents/test_agent1.py": """import pytest
from agents.agent1_preprocessor import CorpusPreprocessor

@pytest.mark.asyncio
async def test_agent1_ingestion():
    agent = CorpusPreprocessor()
    text = "This is the first sentence. And here is the second sentence! Wow, a third?"
    metadata = {"year": 2024, "genre": "test"}
    
    segments = await agent.ingest_file(text, metadata)
    assert len(segments) > 0
    assert segments[0].metadata["year"] == 2024
    
@pytest.mark.asyncio
async def test_agent1_empty_file():
    agent = CorpusPreprocessor()
    with pytest.raises(ValueError):
        await agent.ingest_file("   ", {})
""",

    "tests/agents/test_agent2.py": """import pytest
import os
from agents.agent2_pragmatic import PragmaticAnalyzerAgent
from agents.schemas import CognitiveState, CorpusSegment

@pytest.mark.asyncio
async def test_agent2_analyze():
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")
        
    agent = PragmaticAnalyzerAgent()
    segment = CorpusSegment(
        segment_id="test-123",
        raw_text="It's a bit cold in here, isn't it? [Looking at the open window]",
        metadata={}
    )
    state = CognitiveState(session_id="session-1", segment=segment)
    
    output = await agent.execute(state)
    assert output is not None
    assert output.validation_status == "Passed"
    assert len(output.findings) > 0
    
    # Check if implicature was detected
    theory_text = str([f.linguistic_theory for f in output.findings]).lower()
    assert "act" in theory_text or "implicature" in theory_text or "request" in theory_text
"""
}

def scaffold_phase2():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    print("Phase 2 scaffolding complete.")

if __name__ == "__main__":
    scaffold_phase2()
