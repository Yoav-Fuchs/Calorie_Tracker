import os
import time
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

# Database and Auth
from database import engine, Base, get_db, User, FoodLog
from auth import verify_password, get_password_hash, create_access_token, get_current_user

# Import our ML Pipeline
from ml_pipeline import MLPipeline

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Calorie Tracker API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini-based ML Pipeline
ml_pipeline = MLPipeline(api_key=os.getenv("GEMINI_API_KEY"))

# --- Pydantic Schemas ---
class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class NutritionalInfo(BaseModel):
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float

class FoodItem(BaseModel):
    id: int = None
    name: str
    confidence: float = 1.0
    estimated_volume_cm3: float = 0.0
    estimated_weight_g: float = 0.0
    nutrition: NutritionalInfo

class AnalysisResponse(BaseModel):
    items: List[FoodItem]
    processing_time_ms: float

# --- Auth Routes ---

@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully"}

@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# --- App Routes ---

@app.get("/")
def read_root():
    return {"message": "Calorie Tracker API is running"}

@app.get("/logs", response_model=List[FoodItem])
def get_logs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    logs = db.query(FoodLog).filter(FoodLog.user_id == current_user.id).order_by(FoodLog.created_at.desc()).all()
    results = []
    for log in logs:
        results.append(FoodItem(
            id=log.id,
            name=log.name,
            nutrition=NutritionalInfo(
                calories=log.calories,
                protein_g=log.protein_g,
                carbs_g=log.carbs_g,
                fat_g=log.fat_g
            )
        ))
    return results

@app.delete("/logs/{log_id}")
def delete_log(log_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    log = db.query(FoodLog).filter(FoodLog.id == log_id, FoodLog.user_id == current_user.id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    db.delete(log)
    db.commit()
    return {"message": "Log deleted successfully"}

@app.post("/analyze-food", response_model=AnalysisResponse)
async def analyze_food(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    start_time = time.time()
    content = await file.read()
    
    # Run Gemini Vision Pipeline
    ml_results = await ml_pipeline.analyze_image(content)
    
    items = []
    for res in ml_results:
        nut = res.get("nutrition", {})
        
        # Save to database immediately
        new_log = FoodLog(
            user_id=current_user.id,
            name=res.get("name", "Unknown Food"),
            calories=nut.get("calories", 0),
            protein_g=nut.get("protein_g", 0),
            carbs_g=nut.get("carbs_g", 0),
            fat_g=nut.get("fat_g", 0)
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        
        items.append(FoodItem(
            id=new_log.id,
            name=new_log.name,
            confidence=res.get("confidence", 1.0),
            estimated_volume_cm3=res.get("estimated_volume_cm3", 0.0),
            estimated_weight_g=res.get("estimated_weight_g", 0.0),
            nutrition=NutritionalInfo(
                calories=new_log.calories,
                protein_g=new_log.protein_g,
                carbs_g=new_log.carbs_g,
                fat_g=new_log.fat_g
            )
        ))
        
    processing_time = (time.time() - start_time) * 1000

    return AnalysisResponse(
        items=items,
        processing_time_ms=processing_time
    )
