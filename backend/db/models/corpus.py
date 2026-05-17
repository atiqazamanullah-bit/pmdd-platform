from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from backend.db.base import Base

class Corpus(Base):
    __tablename__ = "corpora"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True)
    token_count = Column(Integer)
    s3_uri = Column(String)
