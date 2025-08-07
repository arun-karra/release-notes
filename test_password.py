#!/usr/bin/env python3
"""
Test script to debug password authentication issues
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_password_setup():
    """Test password setup and configuration"""
    print("🔐 Password Setup Debug")
    print("=" * 50)
    
    # Test 1: Check .env file
    print("\n1. Checking .env file:")
    env_password = os.getenv('APP_PASSWORD')
    if env_password:
        print(f"   ✅ APP_PASSWORD found in .env: {'*' * len(env_password)} (length: {len(env_password)})")
    else:
        print("   ❌ APP_PASSWORD not found in .env")
    
    # Test 2: Check if .env file exists
    print("\n2. Checking .env file existence:")
    if os.path.exists('.env'):
        print("   ✅ .env file exists")
        # Read the .env file to see what's in it
        with open('.env', 'r') as f:
            env_content = f.read()
            if 'APP_PASSWORD' in env_content:
                print("   ✅ APP_PASSWORD found in .env file content")
            else:
                print("   ❌ APP_PASSWORD not found in .env file content")
    else:
        print("   ❌ .env file does not exist")
    
    # Test 3: Check environment variable loading
    print("\n3. Testing environment variable loading:")
    test_password = "test123"
    os.environ['APP_PASSWORD'] = test_password
    loaded_password = os.getenv('APP_PASSWORD')
    if loaded_password == test_password:
        print("   ✅ Environment variable loading works correctly")
    else:
        print("   ❌ Environment variable loading failed")
    
    # Clean up test
    if 'APP_PASSWORD' in os.environ and os.environ['APP_PASSWORD'] == test_password:
        del os.environ['APP_PASSWORD']
    
    # Test 4: Check for common issues
    print("\n4. Common issues to check:")
    print("   - Make sure there are no spaces around the = in .env file")
    print("   - Make sure the password is not wrapped in quotes unless needed")
    print("   - Make sure the .env file is in the root directory")
    print("   - Make sure you've restarted the Streamlit app after changing .env")
    
    # Test 5: Show .env file format
    print("\n5. Correct .env file format:")
    print("   APP_PASSWORD=your_password_here")
    print("   (no spaces around =, no quotes unless password contains spaces)")
    
    return env_password is not None

if __name__ == "__main__":
    test_password_setup()
