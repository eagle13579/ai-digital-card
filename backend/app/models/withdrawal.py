from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Withdrawal(Base):
    __tablename__ = "withdrawal"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
