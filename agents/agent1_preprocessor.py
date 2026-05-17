import uuid
import logging
from typing import List, Dict, Any
from agents.schemas import CorpusSegment

logger = logging.getLogger("pmdd.agent1")

class CorpusPreprocessor:
    """Agent 1: Handles ingestion, normalization, and chunking."""
    
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
        """Validates and chunks raw text into manageable segments."""
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
        text = text.replace("\x00", "")
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
