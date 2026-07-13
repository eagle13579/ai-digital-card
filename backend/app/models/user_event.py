from sqlalchemy import Column, Integer
from app.database import Base


class UserEvent(Base):
    __tablename__ = "user_event"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
