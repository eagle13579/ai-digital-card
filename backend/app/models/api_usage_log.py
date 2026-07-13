from sqlalchemy import Column, Integer
from app.database import Base


class ApiUsageLog(Base):
    __tablename__ = "api_usage_log"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
