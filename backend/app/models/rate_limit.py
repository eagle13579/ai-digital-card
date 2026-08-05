from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class RateLimitRecord(Base):
    __tablename__ = "rate_limit_record"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
