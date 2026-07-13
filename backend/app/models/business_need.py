from sqlalchemy import Column, Integer
from app.database import Base


class BusinessNeed(Base):
    __tablename__ = "business_need"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
