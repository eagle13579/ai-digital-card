from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class OnlineMatchingFeedback(Base):
    __tablename__ = "online_matching_feedback"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)


class OnlineMatchingEvent(Base):
    __tablename__ = "online_matching_events"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)


class OnlineMatchingRegistration(Base):
    __tablename__ = "online_matching_registrations"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
