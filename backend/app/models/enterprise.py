from sqlalchemy import Column, Integer
from app.database import Base


class Enterprise(Base):
    __tablename__ = "enterprise"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)


class EnterpriseRelation(Base):
    __tablename__ = "enterprise_relation"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
