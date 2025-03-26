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
    """Handle API requests with proper return values"""
    if st.query_params.get("api") != "true":
        return None  # Not an API request
        
    try:
        body = st.text_area("", value="", height=1, key="__api_request__", label_visibility="collapsed")
        if not body:
            return {"error": "Empty request body"}, 400
            
        data = json.loads(body)
        
        if not data or 'lead' not in data:
            return {"error": "Invalid request format"}, 400
            
        lead = data['lead']
        campaigns = fetch_campaigns()
        
        if not campaigns:
            return {"error": "No campaigns available"}, 404
            
        # Your actual assignment logic here
        assigned_campaign = campaigns[0]  # Replace with your logic
        
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

# Handle API request
api_response = handle_api_request()

# If API request, show JSON and stop execution
if st.query_params.get("api") == "true":
    if api_response is None:
        st.json({"error": "Invalid API request"})
    else:
        response, status_code = api_response  # Now safe to unpack
        st.json(response)
    st.stop()  # Critical - prevents Streamlit UI from rendering

# Normal Streamlit UI
st.title("Lead Assignment System")
# ... rest of your UI code ...