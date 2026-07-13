from sqlalchemy import Column, Integer
from app.database import Base


class Deal(Base):
    __tablename__ = "deal"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)


class DealActivity(Base):
    __tablename__ = "deal_activity"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
