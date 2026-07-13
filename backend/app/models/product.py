from sqlalchemy import Column, Integer
from app.database import Base


class Product(Base):
    __tablename__ = "product"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
