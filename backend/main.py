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

import json

class NutritionalInfo(BaseModel):
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float

class FoodItem(BaseModel):
    name: str
    confidence: float = 1.0
    estimated_volume_cm3: float = 0.0
    estimated_weight_g: float = 0.0
    nutrition: NutritionalInfo

class MealLogResponse(BaseModel):
    id: int
    name: str
    nutrition: NutritionalInfo
    items: List[FoodItem]

class AnalysisResponse(BaseModel):
    meal: MealLogResponse
    processing_time_ms: float

# --- Auth Routes ---

@app.post("/debug-register")
def debug_register(user: UserCreate):
    from database import SessionLocal
    try:
        db = SessionLocal()
        db_user = db.query(User).filter(User.username == user.username).first()
        if db_user:
            return {"error": "Username already registered"}
        hashed_password = get_password_hash(user.password)
        new_user = User(username=user.username, password_hash=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        db.close()
        return {"message": "Success"}
    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}

@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        db_user = db.query(User).filter(User.username == user.username).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Username already registered")
        hashed_password = get_password_hash(user.password)
        new_user = User(username=user.username, password_hash=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"message": "User registered successfully"}
    except Exception as e:
        import traceback
        raise HTTPException(status_code=400, detail=str(e) + "\n" + traceback.format_exc())

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

@app.get("/logs", response_model=List[MealLogResponse])
def get_logs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    logs = db.query(FoodLog).filter(FoodLog.user_id == current_user.id).order_by(FoodLog.created_at.desc()).all()
    results = []
    for log in logs:
        try:
            items = json.loads(log.items_json) if log.items_json else []
        except:
            items = []
            
        results.append(MealLogResponse(
            id=log.id,
            name=log.name,
            nutrition=NutritionalInfo(
                calories=log.calories,
                protein_g=log.protein_g,
                carbs_g=log.carbs_g,
                fat_g=log.fat_g
            ),
            items=[FoodItem(**item) for item in items]
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
    print(f"\n[{current_user.username}] Uploaded image for analysis: {file.filename}")
    start_time = time.time()
    content = await file.read()
    print(f"Image size: {len(content) / 1024:.2f} KB")
    
    # Run Gemini Vision Pipeline
    ml_results = await ml_pipeline.analyze_image(content)
    
    if not ml_results:
        print("No food items found or API failed.")
        raise HTTPException(status_code=400, detail="Failed to analyze image.")
        
    print(f"Found {len(ml_results)} food items!")
    
    total_calories = 0
    total_protein = 0
    total_carbs = 0
    total_fat = 0
    
    items_list = []
    
    for res in ml_results:
        nut = res.get("nutrition", {})
        total_calories += float(nut.get("calories", 0))
        total_protein += float(nut.get("protein_g", 0))
        total_carbs += float(nut.get("carbs_g", 0))
        total_fat += float(nut.get("fat_g", 0))
        
        items_list.append({
            "name": res.get("name", "Unknown Food"),
            "confidence": float(res.get("confidence", 1.0)),
            "estimated_volume_cm3": float(res.get("estimated_volume_cm3", 0.0)),
            "estimated_weight_g": float(res.get("estimated_weight_g", 0.0)),
            "nutrition": nut
        })
        
    meal_name = f"Meal ({len(items_list)} items)"
    if len(items_list) == 1:
        meal_name = items_list[0]["name"]
        
    # Save a single Meal log
    new_log = FoodLog(
        user_id=current_user.id,
        name=meal_name,
        calories=total_calories,
        protein_g=total_protein,
        carbs_g=total_carbs,
        fat_g=total_fat,
        items_json=json.dumps(items_list)
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    
    meal_response = MealLogResponse(
        id=new_log.id,
        name=new_log.name,
        nutrition=NutritionalInfo(
            calories=new_log.calories,
            protein_g=new_log.protein_g,
            carbs_g=new_log.carbs_g,
            fat_g=new_log.fat_g
        ),
        items=[FoodItem(**item) for item in items_list]
    )

    processing_time = (time.time() - start_time) * 1000

    return AnalysisResponse(
        meal=meal_response,
        processing_time_ms=processing_time
    )
