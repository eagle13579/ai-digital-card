from sqlalchemy import Column, Integer
from app.database import Base


class RateLimitRecord(Base):
    __tablename__ = "rate_limit_record"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
