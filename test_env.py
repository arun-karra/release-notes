#!/usr/bin/env python3
"""
Test script to verify environment variable handling
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_env_vars():
    """Test environment variable handling"""
    print("🔍 Testing Environment Variables...")
    
    # Test Linear API key
    linear_key = os.getenv('LINEAR_API_KEY')
    if linear_key:
        print(f"✅ LINEAR_API_KEY found: {linear_key[:10]}...")
    else:
        print("❌ LINEAR_API_KEY not found")
    
    # Test Notion token
    notion_token = os.getenv('NOTION_TOKEN')
    if notion_token:
        print(f"✅ NOTION_TOKEN found: {notion_token[:10]}...")
    else:
        print("❌ NOTION_TOKEN not found")
    
    # Test Notion database ID
    notion_db = os.getenv('NOTION_DATABASE_ID')
    if notion_db:
        print(f"✅ NOTION_DATABASE_ID found: {notion_db}")
    else:
        print("⚠️  NOTION_DATABASE_ID not found (optional)")
    
    # Test Notion parent page ID
    notion_page = os.getenv('NOTION_PARENT_PAGE_ID')
    if notion_page:
        print(f"✅ NOTION_PARENT_PAGE_ID found: {notion_page}")
    else:
        print("⚠️  NOTION_PARENT_PAGE_ID not found (optional)")

if __name__ == "__main__":
    test_env_vars()
