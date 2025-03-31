# powerbi_connector.py
import pandas as pd
from pymongo import MongoClient

def get_booking_data():
    """Extract booking data and convert to pandas DataFrame for Power BI"""
    client = MongoClient("mongodb+srv://tithee:tithee@cluster0.elvlqwp.mongodb.net/")
    db = client["sports_db"]
    collection = db["booking"]
    
    # Convert MongoDB cursor to DataFrame
    data = list(collection.find())
    df = pd.DataFrame(data)
    
    # Clean and transform data
    if '_id' in df.columns:
        df.drop('_id', axis=1, inplace=True)
    
    return df

def get_inventory_data():
    """Extract inventory data and convert to pandas DataFrame for Power BI"""
    client = MongoClient("mongodb+srv://tithee:tithee@cluster0.elvlqwp.mongodb.net/")
    db = client["sports_db"]
    collection = db["Inventory"]
    
    # Convert MongoDB cursor to DataFrame
    data = list(collection.find())
    df = pd.DataFrame(data)
    
    # Clean and transform data
    if '_id' in df.columns:
        df.drop('_id', axis=1, inplace=True)
    
    return df