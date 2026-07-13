from sqlalchemy import Column, Integer
from app.database import Base


class MatchCreditLog(Base):
    __tablename__ = "match_credit_log"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
