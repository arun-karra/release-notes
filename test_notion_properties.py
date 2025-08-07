#!/usr/bin/env python3
"""
Test script for enhanced Notion properties
"""

import os
from dotenv import load_dotenv
from notion_integration import NotionIntegration

# Load environment variables
load_dotenv()

def test_notion_properties():
    """Test the enhanced Notion properties functionality"""
    print("🔍 Testing Enhanced Notion Properties")
    print("=" * 50)
    
    # Check token
    notion_token = os.getenv('NOTION_TOKEN')
    if not notion_token:
        print("❌ NOTION_TOKEN not found")
        return False
    
    print(f"✅ NOTION_TOKEN found: {notion_token[:10]}...")
    
    try:
        notion = NotionIntegration()
        print("✅ NotionIntegration initialized")
        
        # Test database schema retrieval
        db_id = os.getenv('NOTION_DATABASE_ID')
        if db_id:
            print(f"\n🔍 Testing database schema for: {db_id}")
            schema = notion._get_database_schema(db_id)
            print(f"Found {len(schema)} properties:")
            for prop_name, prop_details in schema.items():
                prop_type = prop_details.get('type', 'unknown')
                print(f"  - {prop_name} ({prop_type})")
        
        # Test property extraction
        print("\n🔍 Testing property extraction:")
        test_content = """
# Changelog - 106.5.0

## 🐛 Bug Fixes
- Fixed issue with user authentication
- Resolved data synchronization problems

## ✨ New Features
- Added dark mode support
- Implemented real-time notifications

## ⚡ Improvements
- Enhanced performance by 25%
- Improved user interface responsiveness
        """
        
        categories = notion._extract_categories(test_content)
        print(f"Extracted categories: {categories}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_notion_properties()
