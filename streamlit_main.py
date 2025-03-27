import streamlit as st
import requests
from datetime import datetime

# Base URL of your running FastAPI application
BASE_URL = "http://localhost:8000"

# Set the page title
st.title("Food Waste Prediction Dashboard")

# Section 1: Add a New Inventory Item
st.header("Add a New Inventory Item")
with st.form(key="inventory_form"):
    item_id = st.number_input("Item ID", min_value=1, step=1, value=5)
    category = st.text_input("Category", value="Bakery")
    store_id = st.text_input("Store ID", value="store5")
    quantity = st.number_input("Quantity", min_value=0.0, value=12.0)
    shelf_life_days = st.number_input("Shelf Life (Days)", min_value=1, step=1, value=5)
    days_on_shelf = st.number_input("Days on Shelf", min_value=0, step=1, value=4)
    price = st.number_input("Price", min_value=0.0, value=3.99)
    timestamp = st.text_input("Timestamp (YYYY-MM-DDTHH:MM:SS)", value="2023-01-05T00:00:00")
    wasted = st.checkbox("Wasted", value=False)
    submit_button = st.form_submit_button(label="Add Inventory Item")

    if submit_button:
        payload = {
            "item_id": int(item_id),
            "category": category,
            "store_id": store_id,
            "quantity": float(quantity),
            "shelf_life_days": int(shelf_life_days),
            "days_on_shelf": int(days_on_shelf),
            "price": float(price),
            "timestamp": timestamp,
            "wasted": wasted
        }
        try:
            response = requests.post(f"{BASE_URL}/api/inventory/", json=payload)
            response.raise_for_status()
            data = response.json()
            st.success(f"Inventory item added successfully! Inventory ID: {data['id']}")
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to add inventory item: {str(e)}")

# Section 2: Retrieve Waste Predictions
st.header("Waste Predictions")
if st.button("Get Waste Predictions"):
    try:
        response = requests.get(f"{BASE_URL}/api/waste-prediction/")
        response.raise_for_status()
        predictions = response.json()
        if predictions:
            st.write("### Predictions")
            for pred in predictions:
                st.write(f"- Inventory ID: {pred['inventory_id']}, Item ID: {pred['item_id']}, Store ID: {pred['store_id']}, Category: {pred['category']}, Waste Probability: {pred['waste_probability']:.2f}, Price: ${pred['price']:.2f}, Quantity: {pred['quantity']:.2f}")
        else:
            st.info("No predictions available.")
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to retrieve waste predictions: {str(e)}")

# Section 3: Retrieve Recommendations
st.header("Recommendations")
if st.button("Get Recommendations"):
    try:
        response = requests.get(f"{BASE_URL}/api/recommendations/")
        response.raise_for_status()
        recommendations = response.json()
        if recommendations:
            st.write("### Recommendations")
            for rec in recommendations:
                st.write(f"- Item ID: {rec['item_id']}, Store ID: {rec['store_id']}, Category: {rec['category']}, Recommendation: {rec['recommendation']}, Priority: {rec['priority']}")
        else:
            st.info("No recommendations available.")
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to retrieve recommendations: {str(e)}")
