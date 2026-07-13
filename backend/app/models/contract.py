from sqlalchemy import Column, Integer
from app.database import Base


class Contract(Base):
    __tablename__ = "contract"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)


class PaymentTransaction(Base):
    __tablename__ = "payment_transaction"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
