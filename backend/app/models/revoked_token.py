from sqlalchemy import Column, Integer
from app.database import Base


class RevokedToken(Base):
    __tablename__ = "revoked_token"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
