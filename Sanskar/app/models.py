from sqlalchemy import Column, Integer, String, Float, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class College(Base):
    __tablename__ = "colleges"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(Integer, nullable=False)
    name = Column(String)
    status = Column(String)
    university = Column(String)

    __table_args__ = (
        UniqueConstraint("code", "name", "status", name="unique_college_code_name_status"),
    )


class Cutoff(Base):
    __tablename__ = "cutoffs"

    id = Column(Integer, primary_key=True, index=True)
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=False)  # ✅ correct FK
    college_code = Column(Integer, nullable=False)  # ✅ still useful
    college = relationship("College", backref="cutoffs")
    branch = Column(String, nullable=False)
    course_code = Column(Integer, nullable=False)
    category = Column(String, nullable=False)
    rank = Column(Integer, nullable=True)
    percent = Column(Float, nullable=True)
    gender = Column(String)
    level = Column(String)  # Home/Other/State level
    year = Column(Integer, default=lambda: datetime.now().year-1)  # Automatically set to current year per instance
    stage = Column(String, default="Stage-I")  # Default to Stage-I
