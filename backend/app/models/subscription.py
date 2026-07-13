from sqlalchemy import Column, Integer
from app.database import Base


class Subscription(Base):
    __tablename__ = "subscription"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
