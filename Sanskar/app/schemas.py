from pydantic import BaseModel

class CutoffOut(BaseModel):
    college: str
    branch: str
    category: str
    rank: int
    percent: float
    gender: str
    level: str

    class Config:
        orm_mode = True
