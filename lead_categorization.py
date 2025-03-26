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

def handle_post_request():
    """Process POST requests from Postman"""
    if st.query_params.get("api") == "true":
        try:
            # Create a hidden text area to capture POST data
            body = st.text_area("POST Data", value="", height=1, 
                              key="postman_data", label_visibility="collapsed")
            
            if not body:
                return {"error": "Empty request body"}, 400
                
            data = json.loads(body)
            
            if not data or 'lead' not in data:
                return {"error": "Missing lead data"}, 400
                
            lead = data['lead']
            campaigns = fetch_campaigns()
            
            if not campaigns:
                return {"error": "No campaigns found"}, 404
                
            # Simple assignment - replace with your logic
            assigned_campaign = campaigns[0]
            
            return {
                "status": "success",
                "assigned_campaign": assigned_campaign['name'],
                "campaign_id": assigned_campaign['id'],
                "smartlead_id": assigned_campaign['smartlead_id'],
                "matched_keywords": assigned_campaign['keywords']
            }, 200
            
        except json.JSONDecodeError:
            return {"error": "Invalid JSON"}, 400
        except Exception as e:
            return {"error": str(e)}, 500

# Handle API request
response, status = handle_post_request()

# If API request, show JSON and stop execution
if st.query_params.get("api") == "true":
    st.header("API Response")
    st.json(response)
    st.stop()  # Critical - prevents Streamlit UI from rendering

# Normal Streamlit UI continues here...
st.title("Lead Assignment Dashboard")
# Rest of your UI code...