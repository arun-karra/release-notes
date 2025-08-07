#!/usr/bin/env python3
"""
Test script for AI summary functionality
"""

import os
from dotenv import load_dotenv
from notion_integration import NotionIntegration

# Load environment variables
load_dotenv()

def test_ai_summary():
    """Test the AI summary functionality"""
    print("🔍 Testing AI Summary Functionality")
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
        
        # Test summary generation
        print("\n🔍 Testing summary generation:")
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
        
        print("Original content:")
        print(test_content)
        
        print("\nGenerating summary...")
        summary = notion._create_simple_summary(test_content)
        
        print("Generated summary:")
        print(summary)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_ai_summary()
