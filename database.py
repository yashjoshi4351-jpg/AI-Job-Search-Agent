from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
try:
    cs = st.secrets["connecter"]
except:
    cs = os.getenv("connecter")

client = MongoClient(cs)
database = client["AI_Job_Search_Agent"]
collection = database["Search_History"]

def search_history(user_query, result):
    history = {
        "resume": user_query,
        "name": result.get("name"),
        "email": result.get("email"),
        "location": result.get("location"),
        "itinerary": result.get("itinerary"),
        "timestamp": datetime.now()
    }
    collection.insert_one(history)

# Get history
def get_history():
    history = collection.find().sort("timestamp", -1)
    results = []
    for item in history:
        results.append(item)
    return results

# Delete single history item explicitly converted to ObjectId
def delete_history(history_id):
    if isinstance(history_id, str):
        collection.delete_one({"_id": ObjectId(history_id)})
    else:
        collection.delete_one({"_id": history_id})

# Clear total history database
def clear_history():
    collection.delete_many({})
