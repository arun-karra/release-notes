import streamlit as st
import requests
import json
import os
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv
import re

# Import Notion integration
try:
    from notion_integration import NotionIntegration
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False

# Load environment variables
load_dotenv()

# Helper function to get environment variables (works for both local and Streamlit Cloud)
def get_env_var(var_name):
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

def is_notion_configured():
    """Check if Notion is properly configured (both import and environment variables)"""
    if not NOTION_AVAILABLE:
        return False
    
    # Check for Notion token - try multiple sources
    notion_token = os.getenv('NOTION_TOKEN')
    
    # If not found locally, try Streamlit secrets
    if not notion_token:
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and st.secrets:
                notion_token = st.secrets.get('NOTION_TOKEN')
        except:
            pass
    
    return bool(notion_token)

def debug_notion_config():
    """Debug function to help troubleshoot Notion configuration"""
    debug_info = {
        'NOTION_AVAILABLE': NOTION_AVAILABLE,
        'env_token': bool(os.getenv('NOTION_TOKEN')),
        'st_secrets_available': False,
        'st_secrets_token': False
    }
    
    try:
        import streamlit as st
        debug_info['st_secrets_available'] = hasattr(st, 'secrets') and bool(st.secrets)
        if debug_info['st_secrets_available']:
            debug_info['st_secrets_token'] = bool(st.secrets.get('NOTION_TOKEN'))
    except:
        pass
    
    return debug_info

# Configuration
LINEAR_API_KEY = os.getenv('LINEAR_API_KEY')
LINEAR_API_URL = 'https://api.linear.app/graphql'
LINEAR_WORKSPACE_URL = os.getenv('LINEAR_WORKSPACE_URL', 'https://linear.app/your-workspace')

# Status emojis mapping
STATUS_EMOJIS = {
    "Completed": "✅",
    "Done": "✅",
    "Fixed": "✅",
    "Resolved": "✅",
    "Started": "🔶",
    "In Progress": "🔶",
    "Code Review": "🔶",
    "Ready for Product": "🔍",
    "Product Review": "🔍",
    "Ready for Testing": "🔍",
    "Testing": "🔍",
    "Backlog": "◻️",
    "Unstarted": "◻️",
    "Todo": "◻️"
}

# Category mappings
CATEGORY_MAPPINGS = {
    "Bug": "🐛 Bug Fixes",
    "Feature": "✨ New Features", 
    "Improvement": "⚡ Improvements",
    "Documentation": "📚 Documentation",
    "Refactor": "🔧 Refactoring",
    "Performance": "🚀 Performance Improvements"
}

# Domain areas
DOMAIN_AREAS = [
    "Activity", "Administration", "Assets", "End of Trial", "Forms",
    "Manage Area", "Media Player", "Notifications", "Permissions",
    "Reporting", "Study Events / Visit", "Study Procedures / Assessment",
    "Subjects", "Trial Configuration", "Uploader"
]

EXCLUDED_STATUSES = ["Canceled", "Cancelled", "Duplicate"]

def make_linear_request(query, variables=None):
    """Make a request to Linear API"""
    headers = {
        'Authorization': LINEAR_API_KEY,
        'Content-Type': 'application/json',
    }
    
    payload = {
        'query': query,
        'variables': variables or {}
    }
    
    response = requests.post(LINEAR_API_URL, json=payload, headers=headers)
    return response.json()

def get_issues_by_label(release_label):
    """Fetch issues by release label"""
    query = """
    query IssuesByReleaseLabel($releaseLabel: String!) {
        issues(filter: {
            labels: { name: { eq: $releaseLabel } },
            parent: { null: true }
        }) {
            nodes {
                identifier
                title
                url
                state {
                    name
                }
                labels {
                    nodes {
                        name
                    }
                }
            }
        }
    }
    """
    
    result = make_linear_request(query, {'releaseLabel': release_label})
    if 'errors' in result:
        st.error(f"Error fetching issues: {result['errors']}")
        return []
    
    return result.get('data', {}).get('issues', {}).get('nodes', [])

def get_release_labels():
    """Fetch all release labels from Linear"""
    query = """
    query {
        viewer {
            organization {
                labels {
                    nodes {
                        name
                        createdAt
                        description
                        parent {
                            name
                        }
                    }
                }
            }
        }
    }
    """
    
    result = make_linear_request(query)
    if 'errors' in result:
        st.error(f"Error fetching labels: {result['errors']}")
        return []
    
    labels = result.get('data', {}).get('viewer', {}).get('organization', {}).get('labels', {}).get('nodes', [])
    
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
    
    # Sort by version number (newest first)
    def version_key(label):
        # Extract version number from the beginning of the label name
        version_match = re.match(r'^(\d+\.\d+\.\d+)', label['name'])
        if version_match:
            version = version_match.group(1)
            parts = version.split('.')
            return [int(part) for part in parts]
        return [0, 0, 0]  # Default for non-version labels
    
    release_labels.sort(key=version_key, reverse=True)
    return release_labels

def determine_category(issue):
    """Determine category based on issue labels"""
    issue_labels = [label['name'] for label in issue['labels']['nodes']]
    
    for label in issue_labels:
        if label in CATEGORY_MAPPINGS:
            return CATEGORY_MAPPINGS[label]
    
    return "Other Changes"

def find_domain_area(issue):
    """Find domain area from issue labels"""
    issue_labels = [label['name'] for label in issue['labels']['nodes']]
    
    for label in issue_labels:
        if label in DOMAIN_AREAS:
            return label
    
    return None

def get_status_emoji(issue):
    """Get status emoji for an issue"""
    state_name = issue['state']['name']
    return STATUS_EMOJIS.get(state_name, "")

def should_exclude_issue(issue):
    """Check if issue should be excluded"""
    state_name = issue['state']['name']
    return state_name in EXCLUDED_STATUSES

def generate_release_notes(issues, release_version):
    """Generate release notes markdown"""
    if not issues:
        return "No issues found for this release."
    
    # Filter out excluded issues
    filtered_issues = [issue for issue in issues if not should_exclude_issue(issue)]
    
    # Group issues by category
    categorized_issues = {}
    for category in CATEGORY_MAPPINGS.values():
        categorized_issues[category] = []
    categorized_issues["Other Changes"] = []
    
    # Categorize issues
    for issue in filtered_issues:
        category = determine_category(issue)
        domain_area = find_domain_area(issue)
        status_emoji = get_status_emoji(issue)
        
        categorized_issues[category].append({
            'title': issue['title'],
            'identifier': issue['identifier'],
            'url': issue['url'] or f"{LINEAR_WORKSPACE_URL}/issue/{issue['identifier']}",
            'domain_area': domain_area,
            'status_emoji': status_emoji
        })
    
    # Generate markdown
    markdown = f"# 🚀 Changelog - {release_version}\n\n"
    markdown += f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    
    for category, issues_list in categorized_issues.items():
        if issues_list:
            markdown += f"## {category}\n\n"
            
            for issue in issues_list:
                markdown += f"- {issue['status_emoji']} **{issue['title']}** ([{issue['identifier']}]({issue['url']}))"
                if issue['domain_area']:
                    markdown += f" [{issue['domain_area']}]"
                markdown += "\n"
            
            markdown += "\n"
    
    return markdown

def check_password():
    """Returns `True` if the user had the correct password."""
    
    # Get password from environment variables or Streamlit secrets
    def get_password():
        # First try environment variable
        password = os.getenv('APP_PASSWORD')
        if password:
            return password
        
        # Then try Streamlit secrets
        try:
            if hasattr(st, 'secrets') and st.secrets:
                return st.secrets.get('password')
        except:
            pass
        
        # Default password if none set (for development)
        return "changeme123"

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        correct_password = get_password()
        user_password = st.session_state.get("password", "")
        
        # Debug information (only show if debug mode is enabled)
        if st.session_state.get("debug_password", False):
            st.write(f"Debug: User entered password length: {len(user_password)}")
            st.write(f"Debug: Expected password length: {len(correct_password) if correct_password else 0}")
            st.write(f"Debug: Passwords match: {user_password == correct_password}")
        
        if user_password == correct_password:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password.
        else:
            st.session_state["password_correct"] = False

    # Check if we need to force re-authentication (for password changes)
    current_password = get_password()
    stored_password_hash = st.session_state.get("password_hash", None)
    
    # Create a simple hash of the current password for comparison
    import hashlib
    current_password_hash = hashlib.md5(current_password.encode()).hexdigest()
    
    # If password has changed, clear the session state
    if stored_password_hash and stored_password_hash != current_password_hash:
        st.session_state.clear()
        st.rerun()
    
    # Store the current password hash
    st.session_state["password_hash"] = current_password_hash

    # First run, show inputs for password.
    if "password_correct" not in st.session_state:
        st.markdown("---")
        st.markdown("## 🔐 Authentication Required")
        st.markdown("Please enter the password to access the Linear Release Notes Generator.")
        
        # Debug checkbox (only show in development)
        if os.getenv('DEBUG_PASSWORD') or st.secrets.get('debug_password', False):
            st.session_state["debug_password"] = st.checkbox("🔍 Debug password (development only)")
            
            # Add a clear session button for debugging
            if st.button("🗑️ Clear Session (Debug)", type="secondary"):
                st.session_state.clear()
                st.rerun()
        
        # Create a container for better styling
        with st.container():
            password_input = st.text_input(
                "Password", 
                type="password", 
                on_change=password_entered, 
                key="password",
                help="You can paste your password here using Ctrl+V (Windows/Linux) or Cmd+V (Mac)"
            )
            st.markdown("💡 **Tip**: You can paste your password using **Ctrl+V** (Windows/Linux) or **Cmd+V** (Mac)")
        
        st.markdown("---")
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.markdown("---")
        st.markdown("## 🔐 Authentication Required")
        st.markdown("Please enter the password to access the Linear Release Notes Generator.")
        
        # Debug checkbox (only show in development)
        if os.getenv('DEBUG_PASSWORD') or st.secrets.get('debug_password', False):
            st.session_state["debug_password"] = st.checkbox("🔍 Debug password (development only)")
            
            # Add a clear session button for debugging
            if st.button("🗑️ Clear Session (Debug)", type="secondary"):
                st.session_state.clear()
                st.rerun()
        
        # Create a container for better styling
        with st.container():
            password_input = st.text_input(
                "Password", 
                type="password", 
                on_change=password_entered, 
                key="password",
                help="You can paste your password here using Ctrl+V (Windows/Linux) or Cmd+V (Mac)"
            )
            st.error("😕 Password incorrect. Please try again.")
            st.markdown("💡 **Tip**: You can paste your password using **Ctrl+V** (Windows/Linux) or **Cmd+V** (Mac)")
        
        st.markdown("---")
        return False
    else:
        # Password correct.
        return True

def main():
    st.set_page_config(
        page_title="Linear Release Notes Generator",
        page_icon="🚀",
        layout="wide"
    )
    
    # Password protection
    if not check_password():
        st.stop()  # Do not continue if not authenticated.
    
    # Main content area
    st.title("🚀 Linear Release Notes Generator")
    st.subheader("Generate beautiful release notes from your Linear issues and views.")
    
    # Check if API key is configured
    if not LINEAR_API_KEY:
        st.error("⚠️ LINEAR_API_KEY not found in environment variables. Please set it in your .env file.")
        st.code("LINEAR_API_KEY=your_api_key_here")
        return
    
    # Initialize session state for current release label
    if 'current_release_label' not in st.session_state:
        st.session_state['current_release_label'] = None
    
    # Display stored release notes if they exist
    if 'release_notes' in st.session_state and 'release_version' in st.session_state:
        release_notes = st.session_state['release_notes']
        release_version = st.session_state['release_version']
        
        # Show current release label status
        if st.session_state['current_release_label']:
            st.info(f"🎯 **Currently working with:** {st.session_state['current_release_label']}")
        
        st.subheader(f"Generated Changelog - {release_version}")
        st.markdown(release_notes)
        
        # Download button
        st.download_button(
            label="Download Release Notes",
            data=release_notes,
            file_name=f"changelog-{release_version}.md",
            mime="text/markdown"
        )
        
        # Notion Integration
        if is_notion_configured():
            st.subheader("📝 Sync to Notion")
            st.info("Notion is configured and ready!")
            
            st.info(f"Ready to sync release notes for version: {release_version}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Create New Notion Page", type="secondary", key="create_notion_page"):
                    st.write("Button clicked! Starting Notion page creation...")
                    try:
                        notion = NotionIntegration()
                        database_id = st.session_state.get('selected_database_id')
                        
                        # Debug information
                        st.info(f"Debug: database_id = {database_id}")
                        st.info(f"Debug: release_version = {release_version}")
                        st.info(f"Debug: content length = {len(release_notes)} characters")
                        
                        with st.spinner("Creating Notion page..."):
                            page_id = notion.create_release_notes_page(
                                release_version=release_version,
                                markdown_content=release_notes,
                                database_id=database_id
                            )
                        
                        st.success(f"✅ Created Notion page! [View Page](https://notion.so/{page_id.replace('-', '')})")
                        
                    except Exception as e:
                        st.error(f"❌ Failed to create Notion page: {str(e)}")
                        # Add more detailed error information
                        st.error(f"Error details: {type(e).__name__}: {str(e)}")
                        import traceback
                        st.error(f"Traceback: {traceback.format_exc()}")
            
            with col2:
                if st.button("Update Existing Page", type="secondary", key="update_notion_page"):
                    try:
                        notion = NotionIntegration()
                        database_id = st.session_state.get('selected_database_id')
                        
                        with st.spinner("Searching for existing page..."):
                            existing_page_id = notion.find_existing_page(release_version, database_id)
                        
                        if existing_page_id:
                            with st.spinner("Updating Notion page..."):
                                notion.update_existing_page(existing_page_id, release_notes)
                            st.success(f"✅ Updated existing Notion page! [View Page](https://notion.so/{existing_page_id.replace('-', '')})")
                        else:
                            st.warning("No existing page found for this release. Use 'Create New Notion Page' instead.")
                            
                    except Exception as e:
                        st.error(f"❌ Failed to update Notion page: {str(e)}")
        else:
            st.warning("Notion integration not configured. Please check your settings.")
    
    # Sidebar configuration
    st.sidebar.header("Configuration")
    
    # Add logout button at the top of sidebar
    if st.sidebar.button("🚪 Logout", type="secondary", help="Logout and return to login screen"):
        # Clear all session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.success("✅ Logged out successfully!")
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # Release Label generation only
    st.sidebar.subheader("Release Labels")
    
    # Add refresh button for release labels
    col1, col2 = st.sidebar.columns([3, 1])
    with col1:
        st.markdown("**Available Release Labels**")
    with col2:
        if st.button("🔄", help="Refresh release labels from Linear"):
            # Clear cached labels and force refresh
            if 'cached_release_labels' in st.session_state:
                del st.session_state['cached_release_labels']
            st.rerun()
    
    # Fetch and display release labels (with caching)
    if 'cached_release_labels' not in st.session_state:
        with st.spinner("Fetching release labels..."):
            st.session_state['cached_release_labels'] = get_release_labels()
    
    release_labels = st.session_state['cached_release_labels']
    
    if release_labels:
        st.sidebar.success(f"Found {len(release_labels)} release labels")
        
        # Create a dropdown for release labels
        label_options = [label['name'] for label in release_labels]
        selected_label = st.sidebar.selectbox(
            "Choose a release label",
            ["Select a release label..."] + label_options,
            index=0,
            help="Select a release label from the 'Release' group to generate release notes"
        )
        
        # Determine which label to use
        release_label = None
        if selected_label and selected_label != "Select a release label...":
            release_label = selected_label
        
        # Show current status
        if st.session_state['current_release_label']:
            st.sidebar.info(f"🎯 **Current:** {st.session_state['current_release_label']}")
            
            # Add a clear button
            if st.sidebar.button("🗑️ Clear Current Release", type="secondary", help="Clear the current release and start fresh"):
                # Clear all session state
                for key in ['release_notes', 'release_version', 'current_release_label']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.success("✅ Cleared current release. Ready for a new one!")
                st.rerun()
        
        if st.sidebar.button("Generate Release Notes", type="primary", help="Generate release notes for the selected label"):
            if not release_label:
                st.error("Please select a release label.")
                return
            
            # Clear previous session state when generating new release notes
            if 'release_notes' in st.session_state:
                del st.session_state['release_notes']
            if 'release_version' in st.session_state:
                del st.session_state['release_version']
            
            with st.spinner(f"Fetching issues for release {release_label}..."):
                issues = get_issues_by_label(release_label)
            
            if issues:
                st.success(f"Found {len(issues)} issues for release {release_label}")
                
                # Generate and display release notes
                release_notes = generate_release_notes(issues, release_label)
                
                # Store in session state for persistence
                st.session_state['release_notes'] = release_notes
                st.session_state['release_version'] = release_label
                st.session_state['current_release_label'] = release_label
                
                st.success(f"✅ Release notes generated for **{release_label}**! Check the main content area above.")
                
                # Force a rerun to display the new content
                st.rerun()
            else:
                st.warning(f"No issues found with label '{release_label}'")
    else:
        st.sidebar.warning("No release labels found. Please check your Linear configuration.")
    
    # Display recent activity
    st.sidebar.header("Recent Activity")
    st.sidebar.info("Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # Notion Integration Section
    if NOTION_AVAILABLE:
        st.sidebar.header("📝 Notion Integration")
        
        if is_notion_configured():
            # Automatically set the database ID if available
            if 'selected_database_id' not in st.session_state:
                try:
                    notion = NotionIntegration()
                    databases = notion.get_databases()
                    if databases:
                        # Look for the "Changelog" database
                        for db in databases:
                            title = db.get('title', [{}])[0].get('plain_text', '')
                            if 'changelog' in title.lower():
                                st.session_state['selected_database_id'] = db['id']
                                break
                        # If no "Changelog" database found, use the first one
                        if 'selected_database_id' not in st.session_state and databases:
                            st.session_state['selected_database_id'] = databases[0]['id']
                except Exception as e:
                    st.sidebar.error(f"❌ Notion connection failed: {str(e)}")
        else:
            st.sidebar.warning("⚠️ Notion not configured")
            
            # Add debug information in development
            if st.checkbox("Show debug info", key="debug_notion"):
                debug_info = debug_notion_config()
                st.sidebar.json(debug_info)
            
            st.sidebar.markdown("""
            To enable Notion integration, add to your `.env` file (local) or Streamlit secrets (cloud):
            ```
            NOTION_TOKEN=your_notion_integration_token
            NOTION_DATABASE_ID=your_database_id (optional)
            NOTION_PARENT_PAGE_ID=your_parent_page_id (optional)
            ```
            """)
    else:
        st.sidebar.header("📝 Notion Integration")
        st.sidebar.info("Install notion-client to enable Notion integration")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "Built with ❤️ using Streamlit | "
        "[Linear API](https://developers.linear.app/docs/graphql/working-with-the-graphql-api)"
    )

if __name__ == "__main__":
    main()
