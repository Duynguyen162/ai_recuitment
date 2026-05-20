from sqlalchemy import BIGINT, TIMESTAMP, Column, Enum as SQLEnum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.enum import CvTypeEnum, ParseStatusEnum
from app.db.base import Base


class ParsedCVData(Base):
    __tablename__ = "parsed_cv_data"

    id = Column(BIGINT, primary_key=True, index=True, autoincrement=True)
    application_id = Column(BIGINT, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, unique=True)
    candidate_id = Column(BIGINT, ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type = Column(SQLEnum(CvTypeEnum), nullable=False)
    parse_status = Column(SQLEnum(ParseStatusEnum), nullable=False, default=ParseStatusEnum.pending)
    parsed_json = Column(JSONB, nullable=True)
    raw_text_snapshot = Column(Text, nullable=True)
    parser_version = Column(Text, nullable=True)
    content_hash = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    application = relationship("Application", back_populates="parsed_cv_data")
    candidate_profile = relationship("CandidateProfile")
