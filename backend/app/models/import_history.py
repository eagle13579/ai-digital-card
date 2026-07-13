from sqlalchemy import Column, Integer
from app.database import Base


class ImportHistory(Base):
    __tablename__ = "import_history"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
