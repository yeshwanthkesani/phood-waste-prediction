from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from model import Base, Item, Inventory, WastePrediction
from predictor import predictor
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import pandas as pd



app = FastAPI(title= "Food Waste Prediction API")

DATABASE_URL = "sqlite:///./phood_data.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class InventoryCreate(BaseModel):
    item_id: int
    category: str
    store_id: str
    quantity: float
    shelf_life_days: int
    days_on_shelf: int
    price: float
    timestamp: Optional[datetime] = None
    wasted: Optional[bool] = False

class PredictionResponse(BaseModel):
    inventory_id: int
    item_id: int
    store_id: str
    category: str
    waste_probability: float
    price: float
    quantity: float

class RecommendationResponse(BaseModel):
    item_id: int
    store_id: str
    category: str
    recommendation: str
    priority: str


def initialize_app():
    db = SessionLocal()
    try:
        predictor.train(db)
        print("Predictor initialized with existing data")
    except Exception as e:
        print(f"Error initializing predictor: {str(e)}")
    finally:
        db.close()


@app.post("/api/inventory/", response_model=dict)
async def add_inventory(inventory_data: InventoryCreate, db: Session = Depends(get_db)):
    try:
        timestamp = inventory_data.timestamp or datetime.utcnow()
        item = db.query(Item).filter_by(item_id=inventory_data.item_id, timestamp=timestamp).first()
        if not item:
            item = Item(item_id=inventory_data.item_id, category=inventory_data.category, timestamp=timestamp)
            db.add(item)
            db.flush()
        
        inventory = Inventory(
            item_id=item.id,
            store_id=inventory_data.store_id,
            timestamp=timestamp,
            quantity=inventory_data.quantity,
            shelf_life_days=inventory_data.shelf_life_days,
            wasted=inventory_data.wasted,
            days_on_shelf=inventory_data.days_on_shelf,
            price=inventory_data.price
        )
        db.add(inventory)
        db.flush()
        
        waste_pred = WastePrediction(inventory_id=inventory.id, waste_probability=0.0)
        db.add(waste_pred)
        db.commit()
        
        predictor.train(db)  # Retrain with new data
        return {"message": "Inventory added", "id": inventory.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    

@app.get("/api/waste-prediction/", response_model=list[PredictionResponse])
async def get_waste_prediction(db: Session = Depends(get_db)):
    try:
        current_items = db.query(Inventory).filter_by(wasted=False).all()
        predictions = predictor.get_predictions(current_items)
        
        for pred in predictions:
            waste_pred = db.query(WastePrediction).filter_by(inventory_id=pred['inventory_id']).first()
            if waste_pred:
                waste_pred.waste_probability = pred['waste_probability']
            else:
                db.add(WastePrediction(inventory_id=pred['inventory_id'], waste_probability=pred['waste_probability']))
        db.commit()
        
        return predictions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/recommendations/", response_model=list[RecommendationResponse])
async def get_recommendations(db: Session = Depends(get_db)):
    try:
        current_items = db.query(Inventory).filter_by(wasted=False).all()
        predictions = predictor.get_predictions(current_items)
        recommendations = predictor.generate_recommendations(predictions)
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# Initialize on startup
@app.on_event("startup")
async def startup_event():
    initialize_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)