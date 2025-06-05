from fastapi import FastAPI
from app.database import engine, Base
from app import models
from app.routes import router as college_router

app = FastAPI(title="Maharashtra CAP College Recommender")

# Create tables
Base.metadata.create_all(bind=engine)

# Include routes
app.include_router(college_router)
