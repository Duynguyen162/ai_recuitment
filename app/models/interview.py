from sqlalchemy import Column, BigInteger, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base 

class Interview(Base):
    __tablename__ = "interviews"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    application_id = Column(
        BigInteger,
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False
    )
    interviewer_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    interview_time = Column(DateTime, nullable=False)
    meeting_link = Column(Text, nullable=True)
    location = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    application = relationship(
        "Application",
        back_populates="interviews"
    )

    interviewer = relationship(
        "User",
        back_populates="interviews_conducted"
    )