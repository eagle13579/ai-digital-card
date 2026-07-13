from sqlalchemy import Column, Integer
from app.database import Base


class Wallet(Base):
    __tablename__ = "wallet"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)


class WalletTransaction(Base):
    __tablename__ = "wallet_transaction"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
