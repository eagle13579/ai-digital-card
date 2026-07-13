from sqlalchemy import Column, Integer, String
from app.database import Base


class CrmContact(Base):
    __tablename__ = "crm_contacts"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), default="")


class CrmDeal(Base):
    __tablename__ = "crm_deals"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), default="")


class CrmPipelineStage(Base):
    __tablename__ = "crm_pipeline_stages"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), default="")


class CrmActivity(Base):
    __tablename__ = "crm_activities"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)


class CrmNote(Base):
    __tablename__ = "crm_notes"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
