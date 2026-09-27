import streamlit as st
import requests
import pandas as pd

# Target Backend Server Configurations
API_URL = "http://127.0.0.1:8000"
API_KEY = "EnterpriseAutomationSecret2026"
HEADERS = {"X-API-Key": API_KEY}

st.set_page_config(page_title="Enterprise CRM Automation", layout="wide")
st.title("🎯 Enterprise CRM Lead Synchronization Platform")

# Sidebar - Create / Add New Leads
st.sidebar.header("📥 Sync New Customer Lead")
with st.sidebar.form(key="lead_form", clear_on_submit=True):
    name = st.text_input("Full Name")
    email = st.text_input("Email Address")
    phone = st.text_input("Phone Number")
    company = st.text_input("Company Name")
    submit_button = st.form_submit_button(label="Sync Lead to Database")

if submit_button:
    if not name or not email or not phone or not company:
        st.sidebar.error("⚠️ All fields are mandatory.")
    else:
        payload = {"name": name, "email": email, "phone": phone, "company": company}
        try:
            res = requests.post(f"{API_URL}/api/v1/sync-lead", json=payload, headers=HEADERS)
            if res.status_code == 201:
                st.sidebar.success("🚀 Lead synchronized successfully!")
            else:
                st.sidebar.error(f"Error: {res.json().get('detail')}")
        except Exception as e:
            st.sidebar.error(f"Could not connect to backend engine: {e}")

# Main Window - Real-time Database Viewer
st.header("📊 Active Leads Ledger Analytics")
if st.button("🔄 Refresh Data Ledger"):
    st.rerun()

try:
    response = requests.get(f"{API_URL}/api/v1/leads", headers=HEADERS)
    if response.status_code == 200:
        leads_data = response.json()
        if leads_data:
            df = pd.DataFrame(leads_data)
            # Reorganize table for presentation
            df = df[['id', 'name', 'email', 'phone', 'company', 'sync_timestamp']]
            st.dataframe(df, use_container_width=True)
            
            # Simple metrics visualization
            st.markdown("---")
            col1, col2 = st.columns(2)
            col1.metric(label="Total Synced Enterprise Records", value=len(df))
            col2.metric(label="System Status", value="ONLINE", delta="Synced")
        else:
            st.info("The lead database ledger is currently empty. Add leads in the sidebar to populate records.")
    else:
        st.error("Failed to authenticate secure gateway data feed.")
except Exception as e:
    st.error(f"Waiting for backend engine stream... Ensure crm_engine.py is running. ({e})")