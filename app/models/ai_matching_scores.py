from sqlalchemy import TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import BIGINT, Column, ForeignKey, func,Text,DECIMAL
from sqlalchemy.orm import relationship
from app.db.base import Base
 
class AiMatchingScore(Base):
    __tablename__ = "ai_matching_scores"
    id = Column(BIGINT, primary_key=True, index=True, autoincrement=True)
    application_id = Column(BIGINT, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False , unique=True)
    score = Column(DECIMAL(5,2), nullable=False)
    strengths = Column(JSONB, nullable=True)
    weaknesses = Column(JSONB, nullable=True)
    explanation = Column(Text, nullable=True)
    generated_at = Column(TIMESTAMP,server_default=func.now(),nullable=False)
    
    application = relationship("Application",back_populates="ai_analysis")