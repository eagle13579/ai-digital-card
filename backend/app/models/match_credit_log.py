from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class MatchCreditLog(Base):
    __tablename__ = "match_credit_log"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
