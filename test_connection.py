#!/usr/bin/env python3
"""
Test script to verify Linear API connection and configuration
"""

import os
import requests
from dotenv import load_dotenv
import re # Added for regex matching in test_release_labels

# Load environment variables
load_dotenv()

def test_linear_connection():
    """Test Linear API connection"""
    print("🔍 Testing Linear API connection...")
    
    # Check if API key is set
    api_key = os.getenv('LINEAR_API_KEY')
    if not api_key:
        print("❌ LINEAR_API_KEY not found in environment variables")
        print("Please set it in your .env file")
        return False
    
    if api_key == 'your_linear_api_key_here':
        print("❌ Please replace the placeholder API key in .env file")
        return False
    
    print("✅ LINEAR_API_KEY found")
    
    # Test API connection
    url = 'https://api.linear.app/graphql'
    headers = {
        'Authorization': api_key,
        'Content-Type': 'application/json',
    }
    
    # Simple query to test connection
    query = """
    query {
        viewer {
            id
            name
            email
        }
    }
    """
    
    payload = {
        'query': query
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        if 'errors' in data:
            print(f"❌ API Error: {data['errors']}")
            return False
        
        viewer = data.get('data', {}).get('viewer')
        if viewer:
            print(f"✅ Connected successfully!")
            print(f"   User: {viewer.get('name', 'Unknown')} ({viewer.get('email', 'Unknown')})")
            return True
        else:
            print("❌ Unexpected response format")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_workspace_access():
    """Test workspace access"""
    print("\n🏢 Testing workspace access...")
    
    api_key = os.getenv('LINEAR_API_KEY')
    workspace_url = os.getenv('LINEAR_WORKSPACE_URL', 'https://linear.app/your-workspace')
    
    if workspace_url == 'https://linear.app/your-workspace':
        print("⚠️  LINEAR_WORKSPACE_URL not configured (using default)")
    
    # Test workspace query
    url = 'https://api.linear.app/graphql'
    headers = {
        'Authorization': api_key,
        'Content-Type': 'application/json',
    }
    
    query = """
    query {
        organization {
            id
            name
            teams {
                nodes {
                    id
                    name
                }
            }
        }
    }
    """
    
    payload = {
        'query': query
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        if 'errors' in data:
            print(f"❌ Workspace access error: {data['errors']}")
            return False
        
        organization = data.get('data', {}).get('organization')
        if organization:
            print(f"✅ Workspace access successful!")
            print(f"   Organization: {organization.get('name', 'Unknown')}")
            
            teams = organization.get('teams', {}).get('nodes', [])
            if teams:
                print(f"   Teams found: {len(teams)}")
                for team in teams[:3]:  # Show first 3 teams
                    print(f"     - {team.get('name', 'Unknown')}")
                if len(teams) > 3:
                    print(f"     ... and {len(teams) - 3} more")
            else:
                print("   No teams found")
            
            return True
        else:
            print("❌ No organization data found")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Workspace access failed: {e}")
        return False

def test_views_access():
    """Test views access"""
    print("\n📊 Testing views access...")
    
    api_key = os.getenv('LINEAR_API_KEY')
    url = 'https://api.linear.app/graphql'
    headers = {
        'Authorization': api_key,
        'Content-Type': 'application/json',
    }
    
    query = """
    query {
        viewer {
            organization {
                teams {
                    nodes {
                        id
                        name
                    }
                }
            }
        }
    }
    """
    
    payload = {
        'query': query
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        if 'errors' in data:
            print(f"❌ Views access error: {data['errors']}")
            return False
        
        teams = data.get('data', {}).get('viewer', {}).get('organization', {}).get('teams', {}).get('nodes', [])
        if teams:
            print(f"✅ Teams access successful!")
            print(f"   Teams found: {len(teams)}")
            for team in teams[:5]:  # Show first 5 teams
                print(f"     - {team.get('name', 'Unknown')}")
            if len(teams) > 5:
                print(f"     ... and {len(teams) - 5} more")
            return True
        else:
            print("⚠️  No teams found")
            return True
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Teams access failed: {e}")
        return False

def test_release_labels():
    """Test release labels access"""
    print("\n🏷️ Testing release labels access...")
    
    api_key = os.getenv('LINEAR_API_KEY')
    url = 'https://api.linear.app/graphql'
    headers = {
        'Authorization': api_key,
        'Content-Type': 'application/json',
    }
    
    query = """
    query {
        viewer {
            organization {
                labels {
                    nodes {
                        name
                        createdAt
                        parent {
                            name
                        }
                    }
                }
            }
        }
    }
    """
    
    payload = {
        'query': query
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        if 'errors' in data:
            print(f"❌ Release labels access error: {data['errors']}")
            return False
        
        labels = data.get('data', {}).get('viewer', {}).get('organization', {}).get('labels', {}).get('nodes', [])
        
        # Filter for labels that belong to the "Release" group
        release_labels = []
        for label in labels:
            # Check if the label has a parent group named "Release"
            parent = label.get('parent')
            if parent and parent.get('name') == 'Release':
                release_labels.append(label)
            # Also include labels that start with version numbers (fallback)
            elif re.match(r'^\d+\.\d+\.\d+', label['name']):
                release_labels.append(label)
        
        if release_labels:
            print(f"✅ Release labels access successful!")
            print(f"   Release labels found: {len(release_labels)}")
            for label in release_labels[:5]:  # Show first 5 labels
                print(f"     - {label.get('name', 'Unknown')}")
            if len(release_labels) > 5:
                print(f"     ... and {len(release_labels) - 5} more")
            return True
        else:
            print("⚠️  No release labels found")
            return True
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Release labels access failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Linear Release Notes Generator - Connection Test")
    print("=" * 60)
    
    # Test API connection
    if not test_linear_connection():
        print("\n❌ Connection test failed. Please check your configuration.")
        return
    
    # Test workspace access
    if not test_workspace_access():
        print("\n⚠️  Workspace access test failed. Some features may not work.")
    
    # Test views access
    if not test_views_access():
        print("\n⚠️  Views access test failed. View-based generation may not work.")
    
    # Test release labels access
    if not test_release_labels():
        print("\n⚠️  Release labels access test failed. Label-based generation may not work.")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("\n🎉 Your Linear API is configured correctly!")
    print("You can now run 'streamlit run app.py' to start the application.")

if __name__ == "__main__":
    main()
