from sqlalchemy import Column, Integer
from app.database import Base


class Review(Base):
    __tablename__ = "review"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
