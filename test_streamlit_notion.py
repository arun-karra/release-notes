#!/usr/bin/env python3
"""
Test Streamlit Notion integration
"""

import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    st.title("Notion Integration Test")
    
    # Test environment variables
    st.subheader("Environment Variables")
    
    # Test local env
    notion_token_env = os.getenv('NOTION_TOKEN')
    if notion_token_env:
        st.success(f"✅ NOTION_TOKEN from .env: {notion_token_env[:10]}...")
    else:
        st.error("❌ NOTION_TOKEN not found in .env")
    
    # Test Streamlit secrets
    try:
        if hasattr(st, 'secrets') and st.secrets:
            notion_token_secret = st.secrets.get('NOTION_TOKEN')
            if notion_token_secret:
                st.success(f"✅ NOTION_TOKEN from st.secrets: {notion_token_secret[:10]}...")
            else:
                st.warning("⚠️ NOTION_TOKEN not found in st.secrets")
        else:
            st.warning("⚠️ st.secrets not available")
    except Exception as e:
        st.error(f"❌ Error accessing st.secrets: {e}")
    
    # Test NotionIntegration
    st.subheader("Notion Integration Test")
    try:
        from notion_integration import NotionIntegration
        notion = NotionIntegration()
        st.success("✅ NotionIntegration initialized successfully")
        
        # Test databases
        databases = notion.get_databases()
        st.info(f"Found {len(databases)} databases")
        
        if databases:
            for db in databases[:3]:
                title = db.get('title', [{}])[0].get('plain_text', 'Untitled')
                st.write(f"- {title} ({db['id']})")
        else:
            st.warning("No databases found. Make sure to share your databases with the integration.")
            
    except Exception as e:
        st.error(f"❌ Error with NotionIntegration: {e}")

if __name__ == "__main__":
    main()
