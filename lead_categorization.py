import streamlit as st
import json
import os
from pyairtable import Api
from groq import Groq

# Initialize clients
airtable = Api(st.secrets["AIRTABLE_API_KEY"])
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def fetch_campaigns():
    """Fetch all campaigns from Airtable"""
    try:
        table = airtable.table(st.secrets["AIRTABLE_BASE_ID"], st.secrets["AIRTABLE_TABLE_NAME"])
        records = table.all()
        return [{
            "id": record["id"],
            "name": record["fields"].get("Name"),
            "description": record["fields"].get("Description"),
            "keywords": record["fields"].get("Keywords", []),
            "smartlead_id": record["fields"].get("SmartleadID")
        } for record in records]
    except Exception as e:
        st.error(f"Error fetching campaigns: {e}")
        return None

def get_ai_recommendation(lead, campaigns):
    """Use Groq API to recommend best campaign"""
    try:
        campaign_info = "\n".join(
            f"{idx+1}. {c['name']} (Keywords: {', '.join(c['keywords'])})"
            for idx, c in enumerate(campaigns)
        )
        
        prompt = f"""
        Recommend the best campaign for this lead (respond ONLY with the campaign number):
        
        Lead:
        - Name: {lead.get('name', 'N/A')}
        - Industry: {lead.get('industry', 'N/A')}
        - Keywords: {', '.join(lead.get('keywords', []))}
        
        Available Campaigns:
        {campaign_info}
        """
        
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="mixtral-8x7b-32768",
            temperature=0.3,
            max_tokens=2
        )
        
        return int(response.choices[0].message.content.strip().split('.')[0]) - 1
    except Exception as e:
        st.error(f"AI recommendation failed: {e}")
        return 0

# API Endpoint Handler
def handle_api_request():
    if st.query_params.get("api") == "true":
        try:
            # Get raw body from request
            body = st.text_area("", value="", height=1, key="hidden_textarea", label_visibility="collapsed")
            
            if not body:
                return {"error": "Empty request body"}, 400
                
            data = json.loads(body)
            
            if not data or 'lead' not in data:
                return {"error": "Invalid request format"}, 400
                
            lead = data['lead']
            campaigns = fetch_campaigns()
            
            if not campaigns:
                return {"error": "No campaigns available"}, 404
                
            selected_idx = get_ai_recommendation(lead, campaigns)
            selected_campaign = campaigns[selected_idx]
            
            response = {
                "status": "success",
                "data": {
                    "lead": lead,
                    "assigned_campaign": selected_campaign['name'],
                    "smartlead_campaign_id": selected_campaign['smartlead_id'],
                    "match_reason": f"Matched based on keywords: {', '.join(selected_campaign['keywords'])}"
                }
            }
            
            st.session_state.api_response = response
            return response, 200
            
        except json.JSONDecodeError:
            return {"error": "Invalid JSON"}, 400
        except Exception as e:
            return {"error": str(e)}, 500

# Handle API request first
response, status_code = handle_api_request()

# If this is an API request, show response and stop execution
if st.query_params.get("api") == "true":
    if status_code != 200:
        st.json(response)
        st.stop()
        
    if 'api_response' in st.session_state:
        st.json(st.session_state.api_response)
        st.stop()

# Normal Streamlit UI (only shown for non-API requests)
st.title("Lead Assignment System")

with st.form("lead_form"):
    name = st.text_input("Lead Name", "Example Corp")
    industry = st.text_input("Industry", "Technology")
    keywords = st.text_input("Keywords (comma separated)", "saas,ai,cloud")
    
    if st.form_submit_button("Assign Campaign"):
        lead = {
            "name": name,
            "industry": industry,
            "keywords": [k.strip() for k in keywords.split(",")]
        }
        
        with st.spinner("Processing..."):
            campaigns = fetch_campaigns()
            
            if campaigns:
                selected_idx = get_ai_recommendation(lead, campaigns)
                selected_campaign = campaigns[selected_idx]
                
                st.success("Campaign assigned successfully!")
                st.json({
                    "status": "success",
                    "data": {
                        "lead": lead,
                        "assigned_campaign": selected_campaign['name'],
                        "smartlead_campaign_id": selected_campaign['smartlead_id'],
                        "match_reason": f"Matched based on keywords: {', '.join(selected_campaign['keywords'])}"
                    }
                })
            else:
                st.error("No campaigns available")