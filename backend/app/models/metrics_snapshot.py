from sqlalchemy import Column, Integer
from app.database import Base


class MetricsSnapshot(Base):
    __tablename__ = "metrics_snapshot"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
