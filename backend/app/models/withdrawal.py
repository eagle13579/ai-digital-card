from sqlalchemy import Column, Integer
from app.database import Base


class Withdrawal(Base):
    __tablename__ = "withdrawal"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
