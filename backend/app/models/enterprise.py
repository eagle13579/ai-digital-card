from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Enterprise(Base):
    __tablename__ = "enterprise"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)


class EnterpriseRelation(Base):
    __tablename__ = "enterprise_relation"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
