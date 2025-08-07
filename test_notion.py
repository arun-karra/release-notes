#!/usr/bin/env python3
"""
Test script for Notion integration
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_notion_setup():
    """Test Notion setup and configuration"""
    print("🔍 Testing Notion Integration...")
    
    # Check if Notion token is configured
    notion_token = os.getenv('NOTION_TOKEN')
    if not notion_token:
        print("❌ NOTION_TOKEN not found in environment variables")
        print("Please add NOTION_TOKEN to your .env file")
        return False
    
    if notion_token == 'your_notion_integration_token':
        print("❌ Please replace the placeholder NOTION_TOKEN in .env file")
        return False
    
    print("✅ NOTION_TOKEN found")
    
    # Test Notion connection
    try:
        from notion_integration import NotionIntegration
        notion = NotionIntegration()
        
        # Test getting databases
        databases = notion.get_databases()
        print(f"✅ Notion connection successful! Found {len(databases)} databases.")
        
        if databases:
            print("📊 Available databases:")
            for db in databases[:3]:  # Show first 3 databases
                title = db.get('title', [{}])[0].get('plain_text', 'Untitled')
                print(f"   - {title}")
            if len(databases) > 3:
                print(f"   ... and {len(databases) - 3} more")
        
        return True
        
    except ImportError:
        print("❌ notion-client not installed")
        print("Run: pip install notion-client")
        return False
    except Exception as e:
        print(f"❌ Notion connection failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 Notion Integration Test")
    print("=" * 40)
    
    if test_notion_setup():
        print("\n" + "=" * 40)
        print("✅ Notion integration is ready!")
        print("\n📋 Next steps:")
        print("1. Your Notion integration is configured")
        print("2. You can now sync release notes to Notion")
        print("3. Use the Streamlit app to generate and sync release notes")
    else:
        print("\n" + "=" * 40)
        print("❌ Notion integration needs configuration")
        print("\n🔧 Setup instructions:")
        print("1. Get your Notion integration token from https://www.notion.so/my-integrations")
        print("2. Add NOTION_TOKEN to your .env file")
        print("3. Optionally add NOTION_DATABASE_ID and NOTION_PARENT_PAGE_ID")
        print("4. Run this test again")

if __name__ == "__main__":
    main()
