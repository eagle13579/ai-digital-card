from sqlalchemy import Column, Integer
from app.database import Base


class MembershipOrder(Base):
    __tablename__ = "membership_order"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
