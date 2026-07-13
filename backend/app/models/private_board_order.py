from sqlalchemy import Column, Integer
from app.database import Base


class PrivateBoardOrder(Base):
    __tablename__ = "private_board_order"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
