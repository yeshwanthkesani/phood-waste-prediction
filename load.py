import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model import Item, Inventory, WastePrediction

# Database connection
DATABASE_URL = "sqlite:///./phood_data.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Load and preprocess data
data = pd.read_csv('food-waste-2025.csv', header=None, skiprows=1)
data.columns = data.iloc[0]
data = data.drop(0).reset_index(drop=True)
data = data.dropna(how='any')
data['timestamp'] = pd.to_datetime(data['timestamp'], format='%Y-%m-%d %H:%M:%S')

def load_data_to_db(dataframe):
    """Load data from DataFrame into the database"""
    session = SessionLocal()
    try:
        # Step 1: Load Items
        items_to_add = {}
        for _, row in dataframe.iterrows():
            item_key = (int(row['item_id']), row['timestamp'])
            if item_key not in items_to_add:
                items_to_add[item_key] = Item(
                    item_id=int(row['item_id']),
                    category=row['category'],
                    timestamp=row['timestamp']
                )
        
        session.add_all(items_to_add.values())
        session.commit()  # Commit to get Item IDs
        
        item_id_map = {(item.item_id, item.timestamp): item.id for item in items_to_add.values()}
        
        # Step 2: Load Inventory
        inventory_items = []
        for _, row in dataframe.iterrows():
            item_key = (int(row['item_id']), row['timestamp'])
            inventory = Inventory(
                item_id=item_id_map[item_key],
                store_id=str(row['store_id']),
                timestamp=row['timestamp'],
                quantity=float(row['quantity']),
                shelf_life_days=int(row['shelf_life_days']),
                wasted=bool(int(row['wasted'])),
                days_on_shelf=int(row['days_on_shelf']),
                price=float(row['price'])
            )
            inventory_items.append(inventory)
        
        session.add_all(inventory_items)
        session.commit()  # Commit to get Inventory IDs
        
        # Step 3: Add WastePredictions with explicit ID retrieval
        waste_predictions = []
        for inventory in inventory_items:
            # Ensure the inventory object has an ID
            if inventory.id is None:
                # If ID is None, query the database to find it
                inv = session.query(Inventory).filter(
                    Inventory.item_id == inventory.item_id,
                    Inventory.timestamp == inventory.timestamp,
                    Inventory.store_id == inventory.store_id
                ).first()
                inventory_id = inv.id if inv else None
            else:
                inventory_id = inventory.id
            
            if inventory_id:
                waste_predictions.append(
                    WastePrediction(
                        inventory_id=inventory_id,
                        waste_probability=0.0
                    )
                )
        
        if waste_predictions:
            session.add_all(waste_predictions)
            session.commit()
        
        print(f"Loaded {len(dataframe)} records into database")
        
    except Exception as e:
        session.rollback()
        print(f"Error loading data: {str(e)}")
    finally:
        session.close()

# Load data
load_data_to_db(data)