#!/usr/bin/env python3
"""
Notion Integration for Linear Release Notes Generator
This module handles creating and updating Notion pages with release notes.
"""

import os
import re
from datetime import datetime
from typing import Optional, Dict, List, Any
from notion_client import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class NotionIntegration:
    def __init__(self):
        """Initialize Notion client"""
        # Try to get token from environment variables or Streamlit secrets
        self.notion_token = self._get_env_var('NOTION_TOKEN')
        self.database_id = self._get_env_var('NOTION_DATABASE_ID')
        self.parent_page_id = self._get_env_var('NOTION_PARENT_PAGE_ID')
        
        if not self.notion_token:
            raise ValueError("NOTION_TOKEN not found in environment variables or Streamlit secrets")
        
        self.client = Client(auth=self.notion_token)
    
    def _get_env_var(self, var_name):
        """Get environment variable, checking both os.environ and st.secrets"""
        # First try to get from environment variables (local development)
        value = os.getenv(var_name)
        if value:
            return value
        
        # If not found, try to get from Streamlit secrets (cloud deployment)
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and st.secrets:
                secret_value = st.secrets.get(var_name)
                if secret_value:
                    return secret_value
        except Exception as e:
            # Silently fail if Streamlit is not available
            pass
        
        return None
    
    def create_release_notes_page(self, release_version: str, markdown_content: str, 
                                 database_id: Optional[str] = None) -> str:
        """
        Create a new page in Notion with release notes
        
        Args:
            release_version: Version number (e.g., "106.5.0")
            markdown_content: Markdown content of release notes
            database_id: Optional database ID to create page in
            
        Returns:
            Page ID of the created page
        """
        try:
            # Convert markdown to Notion blocks
            blocks = self._markdown_to_notion_blocks(markdown_content)
            
            # Prepare page properties - start with the required Name property
            properties = {
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": f"Changelog - {release_version}"
                            }
                        }
                    ]
                }
            }
            
            # Try to add additional properties if they exist in the database
            try:
                # Get database schema to see what properties are available
                if database_id:
                    db_properties = self._get_database_schema(database_id)
                    
                    # Add Version if it exists (rich_text, text, or select)
                    if 'Version' in db_properties:
                        prop_type = db_properties['Version'].get('type', 'rich_text')
                        if prop_type == 'rich_text':
                            properties["Version"] = {
                                "rich_text": [
                                    {
                                        "text": {
                                            "content": release_version
                                        }
                                    }
                                ]
                            }
                        elif prop_type == 'text':
                            properties["Version"] = {
                                "text": {
                                    "content": release_version
                                }
                            }
                        elif prop_type == 'select':
                            properties["Version"] = {
                                "select": {
                                    "name": release_version
                                }
                            }
                    
                    # Add Date if it exists (date type)
                    if 'Date' in db_properties:
                        properties["Date"] = {
                            "date": {
                                "start": datetime.now().isoformat()
                            }
                        }
                    
                    # Add Created Date if it exists (date type)
                    if 'Created Date' in db_properties:
                        properties["Created Date"] = {
                            "date": {
                                "start": datetime.now().isoformat()
                            }
                        }
                    
                    # Add Last Modified if it exists (date type)
                    if 'Last Modified' in db_properties:
                        properties["Last Modified"] = {
                            "date": {
                                "start": datetime.now().isoformat()
                            }
                        }
                    
                    # Add Status if it exists (select type)
                    if 'Status' in db_properties:
                        properties["Status"] = {
                            "select": {
                                "name": "Published"
                            }
                        }
                    
                    # Add Type if it exists (select type)
                    if 'Type' in db_properties:
                        properties["Type"] = {
                            "select": {
                                "name": "Release Notes"
                            }
                        }
                    
                    # Add Category if it exists (select or multi_select type)
                    if 'Category' in db_properties:
                        prop_type = db_properties['Category'].get('type', 'select')
                        if prop_type == 'select':
                            properties["Category"] = {
                                "select": {
                                    "name": "Release Notes"
                                }
                            }
                        elif prop_type == 'multi_select':
                            properties["Category"] = {
                                "multi_select": [
                                    {"name": "Release Notes"}
                                ]
                            }
                    
                    # Add Tags if it exists (multi_select type)
                    if 'Tags' in db_properties:
                        # Extract categories from content
                        categories = self._extract_categories(markdown_content)
                        if categories:
                            properties["Tags"] = {
                                "multi_select": [{"name": cat} for cat in categories[:5]]  # Limit to 5 tags
                            }
                    
                    # Add Priority if it exists (select type)
                    if 'Priority' in db_properties:
                        properties["Priority"] = {
                            "select": {
                                "name": "Medium"
                            }
                        }
                    
                    # Add Description if it exists (rich_text type)
                    if 'Description' in db_properties:
                        # Extract first few lines as description
                        lines = markdown_content.split('\n')[:3]
                        description = ' '.join([line.strip() for line in lines if line.strip()])
                        if len(description) > 200:
                            description = description[:197] + "..."
                        
                        properties["Description"] = {
                            "rich_text": [
                                {
                                    "text": {
                                        "content": description
                                    }
                                }
                            ]
                        }
                    
            except Exception as e:
                # If we can't get the database schema, just use basic properties
                print(f"Warning: Could not retrieve database schema: {e}")
                pass
            
            # Create the page
            if database_id:
                # Create in specific database
                page = self.client.pages.create(
                    parent={"database_id": database_id},
                    properties=properties,
                    children=blocks
                )
            elif self.database_id:
                # Create in default database
                page = self.client.pages.create(
                    parent={"database_id": self.database_id},
                    properties=properties,
                    children=blocks
                )
            elif self.parent_page_id:
                # Create as child page
                page = self.client.pages.create(
                    parent={"page_id": self.parent_page_id},
                    properties=properties,
                    children=blocks
                )
            else:
                # Create in user's workspace
                page = self.client.pages.create(
                    properties=properties,
                    children=blocks
                )
            
            return page["id"]
            
        except Exception as e:
            raise Exception(f"Failed to create Notion page: {str(e)}")
    
    def update_existing_page(self, page_id: str, markdown_content: str) -> bool:
        """
        Update an existing Notion page with new release notes
        
        Args:
            page_id: Notion page ID to update
            markdown_content: New markdown content
            
        Returns:
            True if successful
        """
        try:
            # Convert markdown to Notion blocks
            blocks = self._markdown_to_notion_blocks(markdown_content)
            
            # Clear existing content and add new content
            self.client.blocks.children.delete(page_id)
            self.client.blocks.children.append(page_id, children=blocks)
            
            # Try to update the last modified date if the property exists
            try:
                # Get the page to check its properties
                page_properties = self._get_page_properties(page_id)
                
                # Prepare properties to update
                update_properties = {}
                
                # Add Last Modified if it exists
                if 'Last Modified' in page_properties:
                    update_properties["Last Modified"] = {
                        "date": {
                            "start": datetime.now().isoformat()
                        }
                    }
                
                # Add Modified Date if it exists
                if 'Modified Date' in page_properties:
                    update_properties["Modified Date"] = {
                        "date": {
                            "start": datetime.now().isoformat()
                        }
                    }
                
                # Add Updated At if it exists
                if 'Updated At' in page_properties:
                    update_properties["Updated At"] = {
                        "date": {
                            "start": datetime.now().isoformat()
                        }
                    }
                
                # Update properties if any exist
                if update_properties:
                    self.client.pages.update(page_id, properties=update_properties)
                    
            except Exception as e:
                # If we can't update properties, just continue
                print(f"Warning: Could not update page properties: {e}")
                pass
            
            return True
            
        except Exception as e:
            raise Exception(f"Failed to update Notion page: {str(e)}")
    
    def find_existing_page(self, release_version: str, database_id: Optional[str] = None) -> Optional[str]:
        """
        Find an existing page for a specific release version
        
        Args:
            release_version: Version number to search for
            database_id: Optional database ID to search in
            
        Returns:
            Page ID if found, None otherwise
        """
        try:
            search_query = f"Changelog - {release_version}"
            
            if database_id:
                # Search in specific database
                response = self.client.databases.query(
                    database_id=database_id,
                    filter={
                        "property": "Name",
                        "title": {
                            "equals": search_query
                        }
                    }
                )
            elif self.database_id:
                # Search in default database
                response = self.client.databases.query(
                    database_id=self.database_id,
                    filter={
                        "property": "Name",
                        "title": {
                            "equals": search_query
                        }
                    }
                )
            else:
                # Search in all pages
                response = self.client.search(
                    query=search_query,
                    filter={
                        "property": "object",
                        "value": "page"
                    }
                )
            
            if response["results"]:
                return response["results"][0]["id"]
            
            return None
            
        except Exception as e:
            print(f"Warning: Failed to search for existing page: {str(e)}")
            return None
    
    def _markdown_to_notion_blocks(self, markdown_content: str) -> List[Dict[str, Any]]:
        """
        Convert markdown content to Notion blocks
        
        Args:
            markdown_content: Markdown string
            
        Returns:
            List of Notion block objects
        """
        blocks = []
        lines = markdown_content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Handle headers
            if line.startswith('# '):
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"text": {"content": line[2:]}}]
                    }
                })
            elif line.startswith('## '):
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": line[3:]}}]
                    }
                })
            elif line.startswith('### '):
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"text": {"content": line[4:]}}]
                    }
                })
            
            # Handle bullet points
            elif line.startswith('- '):
                # Extract link if present
                link_match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', line)
                if link_match:
                    link_text = link_match.group(1)
                    link_url = link_match.group(2)
                    content = line[2:].replace(f'[{link_text}]({link_url})', link_text)
                    
                    blocks.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [
                                {
                                    "text": {
                                        "content": content,
                                        "link": {"url": link_url}
                                    }
                                }
                            ]
                        }
                    })
                else:
                    blocks.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [{"text": {"content": line[2:]}}]
                        }
                    })
            
            # Handle regular text
            else:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": line}}]
                    }
                })
        
        return blocks
    
    def _extract_categories(self, markdown_content: str) -> List[str]:
        """
        Extract categories from markdown content
        
        Args:
            markdown_content: Markdown string
            
        Returns:
            List of category names
        """
        categories = []
        lines = markdown_content.split('\n')
        
        for line in lines:
            if line.startswith('## '):
                category = line[3:].strip()
                # Remove emojis and clean up
                category = re.sub(r'[^\w\s-]', '', category).strip()
                if category:
                    categories.append(category)
        
        return categories
    
    def _get_database_schema(self, database_id: str) -> dict:
        """
        Get the schema/properties of a database
        
        Args:
            database_id: Notion database ID
            
        Returns:
            Dictionary of database properties
        """
        try:
            database = self.client.databases.retrieve(database_id=database_id)
            return database.get('properties', {})
        except Exception as e:
            print(f"Warning: Could not retrieve database schema: {e}")
            return {}
    
    def _get_page_properties(self, page_id: str) -> dict:
        """
        Get the properties of a page
        
        Args:
            page_id: Notion page ID
            
        Returns:
            Dictionary of page properties
        """
        try:
            page = self.client.pages.retrieve(page_id)
            return page.get('properties', {})
        except Exception as e:
            print(f"Warning: Could not retrieve page properties: {e}")
            return {}
    
    def get_databases(self) -> List[Dict[str, Any]]:
        """
        Get list of available databases
        
        Returns:
            List of database objects
        """
        try:
            response = self.client.search(
                filter={
                    "property": "object",
                    "value": "database"
                }
            )
            return response["results"]
        except Exception as e:
            print(f"Warning: Failed to get databases: {str(e)}")
            return []
    
    def get_pages(self, database_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of pages from a database
        
        Args:
            database_id: Optional database ID
            
        Returns:
            List of page objects
        """
        try:
            if database_id:
                response = self.client.databases.query(database_id=database_id)
            elif self.database_id:
                response = self.client.databases.query(database_id=self.database_id)
            else:
                response = self.client.search(
                    filter={
                        "property": "object",
                        "value": "page"
                    }
                )
            
            return response["results"]
        except Exception as e:
            print(f"Warning: Failed to get pages: {str(e)}")
            return []

def test_notion_connection():
    """Test Notion API connection"""
    try:
        notion = NotionIntegration()
        databases = notion.get_databases()
        print(f"✅ Notion connection successful! Found {len(databases)} databases.")
        return True
    except Exception as e:
        print(f"❌ Notion connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_notion_connection()
