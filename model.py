from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from datetime import datetime

DATABASE_URL = "sqlite:///./phood_data.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Item Table (Time-series catalog of items with uniqueness on item_id and timestamp)
class Item(Base):
    __tablename__ = 'items'
    item_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    category = Column(String, nullable=False)
    # Composite unique constraint on item_id and timestamp
    __table_args__ = (
        UniqueConstraint('item_id', 'timestamp', name='unique_item_timestamp'),
        # Since item_id and timestamp together are unique, we need a separate primary key
        Column('id', Integer, primary_key=True, autoincrement=True),
    )
    inventory = relationship("Inventory", back_populates='item')

# Inventory Table
class Inventory(Base):
    __tablename__ = 'inventory'
    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False, index=True)  # Foreign key to items.id
    store_id = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    quantity = Column(Float, nullable=False)
    shelf_life_days = Column(Integer, nullable=False)
    wasted = Column(Boolean, default=False)
    days_on_shelf = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

    item = relationship('Item', back_populates="inventory")
    waste_prediction = relationship("WastePrediction", uselist=False, back_populates="inventory")

# Waste Prediction Table
class WastePrediction(Base):
    __tablename__ = 'waste_prediction'
    id = Column(Integer, primary_key=True, index=True)
    inventory_id = Column(Integer, ForeignKey("inventory.id"), unique=True)
    waste_probability = Column(Float, nullable=False)
    inventory = relationship("Inventory", back_populates="waste_prediction")

# Create tables
Base.metadata.create_all(bind=engine)