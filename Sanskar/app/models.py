from sqlalchemy import Column, Integer, String, Float
from datetime import datetime
from app.database import Base
from sqlalchemy import UniqueConstraint

class Cutoff(Base):
    __tablename__ = "cutoffs"

    id = Column(Integer, primary_key=True, index=True)
    college = Column(String)
    branch = Column(String)
    category = Column(String)
    rank = Column(Integer, nullable=True)
    percent = Column(Float, nullable=True)
    gender = Column(String)
    level = Column(String)  # Home/Other/State level
    year = Column(Integer, default=datetime.now().year)  # Automatically set to current year
    stage = Column(String, default="Stage-I")  # Default to Stage-I

class College(Base):
    __tablename__ = "colleges"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String)  # e.g., '1150'
    name = Column(String)
    status = Column(String)  # e.g., 'Government', 'Private', 'Aided'
     
    __table_args__ = (
        UniqueConstraint('code', 'name', 'status', name='unique_college_code_name_status'),
    )
