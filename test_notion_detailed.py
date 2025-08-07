#!/usr/bin/env python3
"""
Detailed Notion integration test
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_notion_detailed():
    """Detailed test of Notion integration"""
    print("🔍 Detailed Notion Integration Test")
    print("=" * 50)
    
    # Check token
    notion_token = os.getenv('NOTION_TOKEN')
    if not notion_token:
        print("❌ NOTION_TOKEN not found")
        return False
    
    print(f"✅ NOTION_TOKEN found: {notion_token[:10]}...")
    
    try:
        from notion_integration import NotionIntegration
        notion = NotionIntegration()
        print("✅ NotionIntegration initialized")
        
        # Test basic API access
        print("\n🔍 Testing basic API access...")
        try:
            # Try to get user info to test basic API access
            response = notion.client.users.me()
            print(f"✅ API access successful - User: {response.get('name', 'Unknown')}")
        except Exception as e:
            print(f"❌ API access failed: {e}")
            return False
        
        # Test database access
        print("\n🔍 Testing database access...")
        databases = notion.get_databases()
        print(f"Found {len(databases)} databases")
        
        if databases:
            for db in databases:
                title = db.get('title', [{}])[0].get('plain_text', 'Untitled')
                db_id = db.get('id', 'Unknown')
                print(f"  - {title} ({db_id})")
        else:
            print("⚠️  No databases found")
            print("   This could mean:")
            print("   1. The integration doesn't have access to any databases")
            print("   2. No databases have been shared with the integration")
            print("   3. The integration token doesn't have the right permissions")
        
        # Test specific database if provided
        db_id = os.getenv('NOTION_DATABASE_ID')
        if db_id:
            print(f"\n🔍 Testing specific database: {db_id}")
            try:
                # Try to query the specific database
                response = notion.client.databases.query(database_id=db_id)
                pages = response.get('results', [])
                print(f"✅ Database access successful - Found {len(pages)} pages")
            except Exception as e:
                print(f"❌ Database access failed: {e}")
                print("   Make sure the database is shared with the integration")
        
        return True
        
    except Exception as e:
        print(f"❌ NotionIntegration failed: {e}")
        return False

if __name__ == "__main__":
    test_notion_detailed()
