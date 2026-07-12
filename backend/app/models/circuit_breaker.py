from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class CircuitBreakerState(Base):
    __tablename__ = "circuit_breaker_state"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
