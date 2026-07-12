from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class MembershipOrder(Base):
    __tablename__ = "membership_order"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
