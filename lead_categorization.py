import streamlit as st
import json
from pyairtable import Api
from groq import Groq

# Initialize clients
airtable = Api(st.secrets["AIRTABLE_API_KEY"])
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def fetch_campaigns():
    """Fetch campaigns from Airtable"""
    try:
        table = airtable.table(st.secrets["AIRTABLE_BASE_ID"], st.secrets["AIRTABLE_TABLE_NAME"])
        records = table.all()
        return [{
            "id": record["id"],
            "name": record["fields"].get("Name"),
            "keywords": record["fields"].get("Keywords", []),
            "smartlead_id": record["fields"].get("SmartleadID")
        } for record in records]
    except Exception as e:
        st.error(f"Airtable error: {e}")
        return None

def handle_api_request():
    """Process API requests and return (response, status_code)"""
    try:
        # Get raw POST data from hidden textarea
        body = st.text_area("", value="", height=1, key="__api_data__", label_visibility="collapsed")
        
        if not body:
            return {"error": "Empty request body"}, 400
        
        data = json.loads(body)
        
        if not data or 'lead' not in data:
            return {"error": "Invalid request format"}, 400
            
        lead = data['lead']
        campaigns = fetch_campaigns()
        
        if not campaigns:
            return {"error": "No campaigns available"}, 404
            
        # Your campaign assignment logic here
        assigned_campaign = campaigns[0]  # Replace with your actual logic
        
        return {
            "status": "success",
            "assigned_campaign": assigned_campaign['name'],
            "campaign_id": assigned_campaign['id'],
            "smartlead_id": assigned_campaign['smartlead_id']
        }, 200
        
    except json.JSONDecodeError:
        return {"error": "Invalid JSON"}, 400
    except Exception as e:
        return {"error": str(e)}, 500

# Check if this is an API request
if st.query_params.get("api") == "true":
    response, status_code = handle_api_request()
    st.json(response)
    st.stop()  # Critical - prevents Streamlit UI from rendering

# Normal Streamlit UI
st.title("Lead Assignment Dashboard")
# ... rest of your UI code ...