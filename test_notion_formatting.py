#!/usr/bin/env python3
"""
Test script for enhanced Notion markdown formatting
"""

import os
from dotenv import load_dotenv
from notion_integration import NotionIntegration

# Load environment variables
load_dotenv()

def test_notion_formatting():
    """Test the enhanced markdown formatting functionality"""
    print("🔍 Testing Enhanced Notion Markdown Formatting")
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
        
        # Test markdown formatting
        print("\n🔍 Testing markdown formatting:")
        test_content = """
# 🚀 Changelog - 106.5.0

## 🐛 Bug Fixes
- ✅ **Fix Library/Sites List with old activity removal** (GP-74)
- ✅ **Issue with library activity after removal of old activities** (GP-70)
- ✅ **It is impossible to create study procedure if required form needs signature** (GP-61)

## ✨ New Features
- ✅ **Added dark mode support** for better user experience
- ✅ **Implemented real-time notifications** for instant updates

## ⚡ Improvements
- ✅ **Enhanced performance by 25%** through optimization
- ✅ **Improved user interface responsiveness** for better UX
        """
        
        print("Original markdown:")
        print(test_content)
        
        print("\nConverting to Notion blocks...")
        blocks = notion._markdown_to_notion_blocks(test_content)
        
        print(f"Generated {len(blocks)} blocks:")
        for i, block in enumerate(blocks[:5]):  # Show first 5 blocks
            block_type = block.get('type', 'unknown')
            rich_text = block.get(block_type, {}).get('rich_text', [])
            content = ' '.join([rt.get('text', {}).get('content', '') for rt in rich_text])
            print(f"  {i+1}. {block_type}: {content[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_notion_formatting()
