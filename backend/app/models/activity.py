from sqlalchemy import Column, Integer
from app.database import Base


class Activity(Base):
    __tablename__ = "activity"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)


class Contact(Base):
    __tablename__ = "contact"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
