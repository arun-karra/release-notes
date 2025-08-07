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
            
            page_id = page["id"]
            
            # Generate AI summary and add it to the page
            try:
                self._generate_ai_summary(page_id, markdown_content)
            except Exception as e:
                print(f"Warning: Could not generate AI summary: {e}")
            
            return page_id
            
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
            
            # Clear existing content by getting all blocks and deleting them one by one
            try:
                existing_blocks = self.client.blocks.children.list(page_id)
                for block in existing_blocks.get('results', []):
                    try:
                        self.client.blocks.delete(block['id'])
                    except Exception as e:
                        print(f"Warning: Could not delete block {block['id']}: {e}")
            except Exception as e:
                print(f"Warning: Could not clear existing content: {e}")
            
            # Add new content
            self.client.blocks.children.append(page_id, children=blocks)
            
            # Generate AI summary and add it to the page
            try:
                self._generate_ai_summary(page_id, markdown_content)
            except Exception as e:
                print(f"Warning: Could not generate AI summary: {e}")
            
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
        Convert markdown content to Notion blocks with proper rich text formatting
        
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
                rich_text = self._parse_rich_text(line[2:])
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": rich_text
                    }
                })
            elif line.startswith('## '):
                rich_text = self._parse_rich_text(line[3:])
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": rich_text
                    }
                })
            elif line.startswith('### '):
                rich_text = self._parse_rich_text(line[4:])
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": rich_text
                    }
                })
            
            # Handle bullet points
            elif line.startswith('- '):
                content = line[2:]
                rich_text = self._parse_rich_text(content)
                
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": rich_text
                    }
                })
            
            # Handle numbered lists
            elif re.match(r'^\d+\. ', line):
                content = re.sub(r'^\d+\. ', '', line)
                rich_text = self._parse_rich_text(content)
                
                blocks.append({
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {
                        "rich_text": rich_text
                    }
                })
            
            # Handle regular text
            else:
                rich_text = self._parse_rich_text(line)
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": rich_text
                    }
                })
        
        return blocks
    
    def _parse_rich_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse markdown text and convert to Notion rich text format
        
        Args:
            text: Markdown text string
            
        Returns:
            List of rich text objects
        """
        rich_text = []
        current_pos = 0
        
        # Handle links first (they can contain other formatting)
        while True:
            link_match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', text[current_pos:])
            if not link_match:
                break
            
            link_start = current_pos + link_match.start()
            link_end = current_pos + link_match.end()
            
            # Add text before the link
            if link_start > current_pos:
                before_text = text[current_pos:link_start]
                rich_text.extend(self._parse_inline_formatting(before_text))
            
            # Add the link
            link_text = link_match.group(1)
            link_url = link_match.group(2)
            rich_text.append({
                "text": {
                    "content": link_text,
                    "link": {"url": link_url}
                }
            })
            
            current_pos = link_end
        
        # Add remaining text
        if current_pos < len(text):
            remaining_text = text[current_pos:]
            rich_text.extend(self._parse_inline_formatting(remaining_text))
        
        return rich_text
    
    def _parse_inline_formatting(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse inline markdown formatting (bold, italic, etc.)
        
        Args:
            text: Text with inline formatting
            
        Returns:
            List of rich text objects
        """
        if not text:
            return []
        
        rich_text = []
        current_pos = 0
        
        # Handle bold text (**text**)
        while True:
            bold_match = re.search(r'\*\*([^*]+)\*\*', text[current_pos:])
            if not bold_match:
                break
            
            bold_start = current_pos + bold_match.start()
            bold_end = current_pos + bold_match.end()
            
            # Add text before the bold
            if bold_start > current_pos:
                before_text = text[current_pos:bold_start]
                rich_text.extend(self._parse_italic_formatting(before_text))
            
            # Add the bold text
            bold_content = bold_match.group(1)
            rich_text.append({
                "text": {
                    "content": bold_content
                },
                "annotations": {
                    "bold": True
                }
            })
            
            current_pos = bold_end
        
        # Handle remaining text for italic formatting
        if current_pos < len(text):
            remaining_text = text[current_pos:]
            rich_text.extend(self._parse_italic_formatting(remaining_text))
        
        return rich_text
    
    def _parse_italic_formatting(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse italic markdown formatting (*text*)
        
        Args:
            text: Text with italic formatting
            
        Returns:
            List of rich text objects
        """
        if not text:
            return []
        
        rich_text = []
        current_pos = 0
        
        # Handle italic text (*text*)
        while True:
            italic_match = re.search(r'\*([^*]+)\*', text[current_pos:])
            if not italic_match:
                break
            
            italic_start = current_pos + italic_match.start()
            italic_end = current_pos + italic_match.end()
            
            # Add text before the italic
            if italic_start > current_pos:
                before_text = text[current_pos:italic_start]
                rich_text.append({
                    "text": {
                        "content": before_text
                    }
                })
            
            # Add the italic text
            italic_content = italic_match.group(1)
            rich_text.append({
                "text": {
                    "content": italic_content
                },
                "annotations": {
                    "italic": True
                }
            })
            
            current_pos = italic_end
        
        # Add remaining text
        if current_pos < len(text):
            remaining_text = text[current_pos:]
            rich_text.append({
                "text": {
                    "content": remaining_text
                }
            })
        
        return rich_text
    
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

    def _generate_ai_summary(self, page_id: str, markdown_content: str) -> bool:
        """
        Generate an AI summary of the changelog using Notion AI
        
        Args:
            page_id: Notion page ID to add summary to
            markdown_content: Original markdown content
            
        Returns:
            True if successful
        """
        try:
            # Check if summary already exists
            existing_blocks = self.client.blocks.children.list(page_id)
            for block in existing_blocks.get('results', []):
                if block.get('type') == 'heading_2':
                    rich_text = block.get('heading_2', {}).get('rich_text', [])
                    if rich_text and any('summary' in rt.get('text', {}).get('content', '').lower() for rt in rich_text):
                        print("Summary already exists, skipping...")
                        return True
            
            # Create a simple summary (since Notion AI API might not be publicly available)
            summary = self._create_simple_summary(markdown_content)
            
            # Add the summary to the page
            self.client.blocks.children.append(
                page_id,
                children=[
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [
                                {
                                    "text": {
                                        "content": "📋 Release Summary"
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "text": {
                                        "content": summary
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "object": "block",
                        "type": "divider",
                        "divider": {}
                    }
                ]
            )
            
            return True
            
        except Exception as e:
            print(f"Warning: Could not generate AI summary: {e}")
            return False
    
    def _create_simple_summary(self, markdown_content: str) -> str:
        """
        Create a simple summary when AI is not available
        
        Args:
            markdown_content: Original markdown content
            
        Returns:
            Simple summary string
        """
        try:
            # Extract key information from the changelog
            lines = markdown_content.split('\n')
            summary_parts = []
            
            # Count different types of changes
            bug_fixes = 0
            new_features = 0
            improvements = 0
            other_changes = 0
            
            current_section = ""
            
            for line in lines:
                line = line.strip()
                if line.startswith('## 🐛 Bug Fixes'):
                    current_section = "bug_fixes"
                elif line.startswith('## ✨ New Features'):
                    current_section = "new_features"
                elif line.startswith('## ⚡ Improvements'):
                    current_section = "improvements"
                elif line.startswith('- ') and current_section:
                    if current_section == "bug_fixes":
                        bug_fixes += 1
                    elif current_section == "new_features":
                        new_features += 1
                    elif current_section == "improvements":
                        improvements += 1
                    else:
                        other_changes += 1
            
            # Create a user-friendly summary
            total_changes = bug_fixes + new_features + improvements + other_changes
            
            if total_changes == 0:
                return "This release includes various updates and improvements to enhance the overall user experience."
            
            summary_parts.append("🎯 **Release Overview**")
            summary_parts.append(f"\nThis release brings {total_changes} total change{'s' if total_changes > 1 else ''} to improve your experience:")
            
            if new_features > 0:
                summary_parts.append(f"• ✨ **{new_features} new feature{'s' if new_features > 1 else ''}** - Exciting additions to enhance functionality")
            
            if improvements > 0:
                summary_parts.append(f"• ⚡ **{improvements} improvement{'s' if improvements > 1 else ''}** - Enhanced performance and user experience")
            
            if bug_fixes > 0:
                summary_parts.append(f"• 🐛 **{bug_fixes} bug fix{'es' if bug_fixes > 1 else ''}** - Resolved issues for smoother operation")
            
            if other_changes > 0:
                summary_parts.append(f"• 🔧 **{other_changes} other change{'s' if other_changes > 1 else ''}** - Additional updates and refinements")
            
            # Add a conclusion
            if new_features > 0:
                summary_parts.append(f"\n🚀 **What's New**: This release introduces {new_features} new feature{'s' if new_features > 1 else ''} that will enhance your workflow.")
            
            if bug_fixes > 0:
                summary_parts.append(f"🔧 **Stability**: {bug_fixes} bug fix{'es' if bug_fixes > 1 else ''} ensure a more reliable experience.")
            
            summary_parts.append("\n💡 **Recommendation**: Update to this version to take advantage of the latest improvements and new features.")
            
            return " ".join(summary_parts)
            
        except Exception as e:
            return "🎯 **Release Overview**\n\nThis release includes various updates and improvements to enhance the overall user experience. We recommend updating to this version to take advantage of the latest features and bug fixes."

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
