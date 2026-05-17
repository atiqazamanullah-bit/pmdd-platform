import os

files = {
    "memory/schemas.py": """from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class EpisodicEvent(BaseModel):
    event_id: str
    agent_id: str
    segment_id: str
    reasoning_trace: str
    applied_theory: str
    validation_score: float = Field(..., ge=0.0, le=1.0)
    was_successful: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RetrievalContext(BaseModel):
    query_text: str
    similar_episodes: List[EpisodicEvent]
    semantic_drift_examples: List[Dict[str, Any]]
    confidence_decay: float = 1.0

class StrategyMetrics(BaseModel):
    theory_name: str
    success_rate: float
    usage_count: int
    average_confidence: float
""",

    "memory/vector_store.py": """import os
import logging
from typing import List, Dict, Any
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings

logger = logging.getLogger("pmdd.memory.vector")

class VectorMemoryManager:
    \"\"\"Handles Pinecone vector database and OpenAI embeddings.\"\"\"
    
    def __init__(self, index_name: str = "pmdd-memory"):
        self.index_name = index_name
        self.pc = None
        self.index = None
        self.embeddings = None
        
        # Initialize if keys are present
        if os.getenv("PINECONE_API_KEY") and os.getenv("OPENAI_API_KEY"):
            self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
            self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
            self._ensure_index()
            
    def _ensure_index(self):
        if self.index_name not in [idx.name for idx in self.pc.list_indexes()]:
            logger.info(f"Creating Pinecone index: {self.index_name}")
            self.pc.create_index(
                name=self.index_name,
                dimension=3072,  # text-embedding-3-large dimension
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
        self.index = self.pc.Index(self.index_name)

    async def embed_and_store(self, texts: List[str], metadatas: List[Dict[str, Any]], ids: List[str]):
        if not self.index:
            logger.warning("Vector index not initialized.")
            return
            
        vectors = await self.embeddings.aembed_documents(texts)
        records = zip(ids, vectors, metadatas)
        
        # Chunking upserts
        batch_size = 100
        records_list = list(records)
        for i in range(0, len(records_list), batch_size):
            self.index.upsert(vectors=records_list[i:i+batch_size])

    async def retrieve_similar(self, query: str, top_k: int = 5, filter: Dict = None) -> List[Dict[str, Any]]:
        if not self.index:
            return []
            
        query_vec = await self.embeddings.aembed_query(query)
        results = self.index.query(
            vector=query_vec,
            top_k=top_k,
            include_metadata=True,
            filter=filter
        )
        return [{"id": match.id, "score": match.score, "metadata": match.metadata} for match in results.matches]
""",

    "memory/episodic.py": """from typing import List, Dict, Any
from memory.schemas import EpisodicEvent
from memory.vector_store import VectorMemoryManager
import uuid
import json

class EpisodicMemoryEngine:
    \"\"\"Stores and retrieves agent reasoning trajectories.\"\"\"
    
    def __init__(self, vector_store: VectorMemoryManager):
        self.vector_store = vector_store
        
    async def log_event(self, event: EpisodicEvent):
        # In a real setup, we also write to Supabase Postgres here.
        text_representation = f"Agent {event.agent_id} analyzed {event.segment_id} using {event.applied_theory}. Success: {event.was_successful}. Trace: {event.reasoning_trace}"
        
        await self.vector_store.embed_and_store(
            texts=[text_representation],
            metadatas=[event.model_dump(mode="json")],
            ids=[event.event_id]
        )

    async def retrieve_lessons(self, query_context: str, theory_filter: str = None) -> List[EpisodicEvent]:
        filter_dict = {"was_successful": True}
        if theory_filter:
            filter_dict["applied_theory"] = theory_filter
            
        results = await self.vector_store.retrieve_similar(query_context, top_k=3, filter=filter_dict)
        events = []
        for r in results:
            # Reconstruct EpisodicEvent from metadata
            events.append(EpisodicEvent(**r["metadata"]))
        return events
""",

    "rag/retriever.py": """from typing import List, Dict, Any
from memory.vector_store import VectorMemoryManager
from memory.episodic import EpisodicMemoryEngine
from memory.schemas import RetrievalContext

class RAGOrchestrator:
    \"\"\"Retrieval Augmented Generation pipeline for Agents.\"\"\"
    
    def __init__(self, vector_store: VectorMemoryManager, episodic_engine: EpisodicMemoryEngine):
        self.vector_store = vector_store
        self.episodic_engine = episodic_engine
        
    async def get_context(self, text_segment: str) -> RetrievalContext:
        \"\"\"Fetches relevant past episodes and semantic drift examples.\"\"\"
        # 1. Retrieve similar successful reasoning paths
        lessons = await self.episodic_engine.retrieve_lessons(text_segment)
        
        # 2. Retrieve pure semantic corpus similarities (drift examples)
        corpus_matches = await self.vector_store.retrieve_similar(text_segment, top_k=2)
        
        return RetrievalContext(
            query_text=text_segment,
            similar_episodes=lessons,
            semantic_drift_examples=corpus_matches
        )
""",

    "rag/adaptive_learning.py": """from typing import List
from memory.schemas import EpisodicEvent, StrategyMetrics

class StrategyAdaptationEngine:
    \"\"\"Learns which linguistic theories work best over time.\"\"\"
    
    def __init__(self):
        self.history: List[EpisodicEvent] = []
        
    def ingest_batch(self, events: List[EpisodicEvent]):
        self.history.extend(events)
        
    def rank_theories(self) -> List[StrategyMetrics]:
        \"\"\"Calculates success rates of different theories based on validation scores.\"\"\"
        stats = {}
        for ev in self.history:
            t = ev.applied_theory
            if t not in stats:
                stats[t] = {"successes": 0, "total": 0, "conf_sum": 0.0}
            stats[t]["total"] += 1
            if ev.was_successful:
                stats[t]["successes"] += 1
            stats[t]["conf_sum"] += ev.validation_score
            
        metrics = []
        for t, data in stats.items():
            metrics.append(StrategyMetrics(
                theory_name=t,
                success_rate=data["successes"] / data["total"] if data["total"] > 0 else 0.0,
                usage_count=data["total"],
                average_confidence=data["conf_sum"] / data["total"] if data["total"] > 0 else 0.0
            ))
            
        # Sort by success rate descending
        return sorted(metrics, key=lambda x: x.success_rate, reverse=True)
""",

    "tests/memory/test_rag.py": """import pytest
from unittest.mock import AsyncMock, MagicMock
from rag.retriever import RAGOrchestrator
from memory.vector_store import VectorMemoryManager
from memory.episodic import EpisodicMemoryEngine
from memory.schemas import RetrievalContext

@pytest.mark.asyncio
async def test_rag_retrieval():
    # Mock Vector Store
    mock_vs = MagicMock(spec=VectorMemoryManager)
    mock_vs.retrieve_similar = AsyncMock(return_value=[{"id": "doc1", "score": 0.9, "metadata": {}}])
    
    # Mock Episodic Engine
    mock_ep = MagicMock(spec=EpisodicMemoryEngine)
    mock_ep.retrieve_lessons = AsyncMock(return_value=[])
    
    rag = RAGOrchestrator(mock_vs, mock_ep)
    context = await rag.get_context("This is a test segment.")
    
    assert isinstance(context, RetrievalContext)
    assert len(context.semantic_drift_examples) == 1
    mock_ep.retrieve_lessons.assert_called_once()
""",

    "tests/memory/test_adaptive.py": """import pytest
from rag.adaptive_learning import StrategyAdaptationEngine
from memory.schemas import EpisodicEvent

def test_strategy_adaptation():
    engine = StrategyAdaptationEngine()
    
    events = [
        EpisodicEvent(event_id="1", agent_id="A2", segment_id="s1", reasoning_trace="...", applied_theory="Speech Act", validation_score=0.9, was_successful=True),
        EpisodicEvent(event_id="2", agent_id="A2", segment_id="s2", reasoning_trace="...", applied_theory="Speech Act", validation_score=0.4, was_successful=False),
        EpisodicEvent(event_id="3", agent_id="A2", segment_id="s3", reasoning_trace="...", applied_theory="Gricean", validation_score=0.95, was_successful=True)
    ]
    
    engine.ingest_batch(events)
    ranking = engine.rank_theories()
    
    assert len(ranking) == 2
    assert ranking[0].theory_name == "Gricean"
    assert ranking[0].success_rate == 1.0
    assert ranking[1].theory_name == "Speech Act"
    assert ranking[1].success_rate == 0.5
"""
}

def scaffold_phase3():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    print("Phase 3 Memory & RAG scaffolding complete.")

if __name__ == "__main__":
    scaffold_phase3()
