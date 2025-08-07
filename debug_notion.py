#!/usr/bin/env python3
"""
Debug script for Notion integration
"""

import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def debug_notion_setup():
    """Debug Notion setup step by step"""
    print("🔍 Debugging Notion Integration...")
    print("=" * 50)
    
    # Test 1: Check environment variables
    print("1. Checking environment variables:")
    notion_token = os.getenv('NOTION_TOKEN')
    if notion_token:
        print(f"   ✅ NOTION_TOKEN found: {notion_token[:10]}...")
    else:
        print("   ❌ NOTION_TOKEN not found in os.getenv()")
    
    # Test 2: Check Streamlit secrets
    print("\n2. Checking Streamlit secrets:")
    try:
        if hasattr(st, 'secrets') and st.secrets:
            st_secret = st.secrets.get('NOTION_TOKEN')
            if st_secret:
                print(f"   ✅ NOTION_TOKEN found in st.secrets: {st_secret[:10]}...")
            else:
                print("   ❌ NOTION_TOKEN not found in st.secrets")
        else:
            print("   ⚠️  st.secrets not available")
    except Exception as e:
        print(f"   ❌ Error accessing st.secrets: {e}")
    
    # Test 3: Test NotionIntegration class
    print("\n3. Testing NotionIntegration class:")
    try:
        from notion_integration import NotionIntegration
        notion = NotionIntegration()
        print("   ✅ NotionIntegration initialized successfully")
        
        # Test 4: Test getting databases
        print("\n4. Testing database access:")
        databases = notion.get_databases()
        print(f"   Found {len(databases)} databases")
        
        if databases:
            for db in databases[:3]:
                title = db.get('title', [{}])[0].get('plain_text', 'Untitled')
                print(f"   - {title} ({db['id']})")
        else:
            print("   ⚠️  No databases found - check if integration has permissions")
            
    except Exception as e:
        print(f"   ❌ Error with NotionIntegration: {e}")
    
    # Test 5: Check all environment variables
    print("\n5. All environment variables:")
    env_vars = ['NOTION_TOKEN', 'NOTION_DATABASE_ID', 'NOTION_PARENT_PAGE_ID']
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: {value[:10] if 'TOKEN' in var else value}...")
        else:
            print(f"   ❌ {var}: not found")

if __name__ == "__main__":
    debug_notion_setup()
