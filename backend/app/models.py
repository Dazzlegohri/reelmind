from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.db import Base

class Reel(Base):
    __tablename__ = "reels"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    path = Column(String(1000), nullable=False)
    status = Column(String(50), default="uploaded")
    duration = Column(String(50), nullable=True)
    transcript = Column(Text, default="")
    analysis_json = Column(Text, default="{}")
    optimized_path = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
