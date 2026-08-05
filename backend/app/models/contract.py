from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Contract(Base):
    __tablename__ = "contract"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)


class PaymentTransaction(Base):
    __tablename__ = "payment_transaction"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
