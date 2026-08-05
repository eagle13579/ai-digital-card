from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class BusinessDeal(Base):
    __tablename__ = "deal"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)


class DealActivity(Base):
    __tablename__ = "deal_activity"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
