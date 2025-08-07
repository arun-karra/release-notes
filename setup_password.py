#!/usr/bin/env python3
"""
Password setup script for Linear Release Notes Generator
"""

import os
import getpass
from dotenv import load_dotenv

def setup_password():
    """Set up password for the application"""
    print("🔐 Password Setup for Linear Release Notes Generator")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = ".env"
    if os.path.exists(env_file):
        print(f"✅ Found existing {env_file} file")
    else:
        print(f"📝 Creating new {env_file} file")
    
    # Get current password if exists
    load_dotenv()
    current_password = os.getenv('APP_PASSWORD')
    
    if current_password:
        print(f"Current password is set: {'*' * len(current_password)}")
        change = input("Do you want to change it? (y/n): ").lower().strip()
        if change != 'y':
            print("Password unchanged.")
            return
    
    # Get new password
    print("\n🔑 Enter a new password:")
    print("   - Must be at least 8 characters")
    print("   - Should be strong and unique")
    print("   - This will be stored in your .env file")
    
    while True:
        password = getpass.getpass("New password: ")
        
        if len(password) < 8:
            print("❌ Password must be at least 8 characters long")
            continue
        
        confirm_password = getpass.getpass("Confirm password: ")
        
        if password != confirm_password:
            print("❌ Passwords don't match. Please try again.")
            continue
        
        break
    
    # Update .env file
    env_lines = []
    password_updated = False
    
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('APP_PASSWORD='):
                    env_lines.append(f'APP_PASSWORD={password}\n')
                    password_updated = True
                else:
                    env_lines.append(line)
    
    if not password_updated:
        env_lines.append(f'APP_PASSWORD={password}\n')
    
    # Write back to .env file
    with open(env_file, 'w') as f:
        f.writelines(env_lines)
    
    print(f"\n✅ Password updated successfully!")
    print(f"📁 Password stored in {env_file}")
    print(f"🔒 Make sure to keep your {env_file} file secure and never commit it to version control")
    
    # Check if .gitignore includes .env
    if os.path.exists('.gitignore'):
        with open('.gitignore', 'r') as f:
            gitignore_content = f.read()
            if '.env' in gitignore_content:
                print("✅ .env file is already in .gitignore (good!)")
            else:
                print("⚠️  Warning: .env file is not in .gitignore")
                print("   Consider adding '.env' to your .gitignore file")
    else:
        print("⚠️  Warning: No .gitignore file found")
        print("   Consider creating a .gitignore file and adding '.env' to it")

if __name__ == "__main__":
    setup_password()
