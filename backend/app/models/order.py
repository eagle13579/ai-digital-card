from sqlalchemy import Column, Integer
from app.database import Base


class Order(Base):
    __tablename__ = "order"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
