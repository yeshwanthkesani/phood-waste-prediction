import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from model import Inventory  # Import Inventory for session queries

class WastePredictor:
    def __init__(self):  # Removed unused 'data' parameter
        self.model = LogisticRegression()
        self.scaler = StandardScaler()
        self.is_trained = False
        self.category_mapping = {}

    def prepare_features(self, inventory):
        days_remaining = max(0, inventory.shelf_life_days - inventory.days_on_shelf)
        category_encoded = self.category_mapping.get(inventory.item.category, 0)
        return np.array([
            days_remaining / inventory.shelf_life_days,
            inventory.quantity,
            inventory.price,
            inventory.days_on_shelf,
            category_encoded
        ]).reshape(1, -1)
    
    def train(self, session):
        """Train the model with all inventory data from the session"""
        inventory_items = session.query(Inventory).all()
        if not inventory_items:
            print("No inventory items found for training.")
            return
        
        self.category_mapping = {cat: i for i, cat in enumerate(set(item.item.category for item in inventory_items))}
        X = np.array([self.prepare_features(item)[0] for item in inventory_items])
        y = np.array([1 if item.wasted else 0 for item in inventory_items])
        
        if len(X) > 0:
            X_scaled = self.scaler.fit_transform(X)
            self.model.fit(X_scaled, y)
            self.is_trained = True
            print("Model trained successfully with", len(inventory_items), "items.")
        else:
            print("No features available for training.")

    def predict_waste(self, inventory):
        """Predict waste probability for a single inventory item"""
        if not self.is_trained:
            print("Model not trained, returning default probability.")
            return 0.5
        features = self.prepare_features(inventory)
        features_scaled = self.scaler.transform(features)
        return self.model.predict_proba(features_scaled)[0][1]

    def get_predictions(self, items):
        """Get predictions for a list of inventory items"""
        return [{
            'inventory_id': item.id,
            'item_id': item.item.item_id,
            'store_id': item.store_id,
            'category': item.item.category,
            'waste_probability': self.predict_waste(item),
            'price': item.price,
            'quantity': item.quantity
        } for item in items]

    def generate_recommendations(self, predictions):
        """Generate recommendations based on predictions"""
        recommendations = []
        for pred in predictions:
            prob = pred['waste_probability']
            if prob > 0.7:
                discount = min(0.5, pred['price'] * max(0.1, prob - 0.5))
                action = f"Apply ${discount:.2f} discount or donate"
                priority = 'high'
            elif prob > 0.4:
                action = "Monitor closely and consider promotion"
                priority = 'medium'
            else:
                continue
            recommendations.append({
                'item_id': pred['item_id'],
                'store_id': pred['store_id'],
                'category': pred['category'],
                'recommendation': action,
                'priority': priority
            })
        return recommendations

# Singleton instance
predictor = WastePredictor()