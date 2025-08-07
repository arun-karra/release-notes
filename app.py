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

def get_views():
    """Fetch all views from Linear"""
    query = """
    query {
        viewer {
            organization {
                teams {
                    nodes {
                        id
                        name
                        cycles {
                            nodes {
                                id
                                name
                                number
                            }
                        }
                    }
                }
            }
        }
    }
    """
    
    result = make_linear_request(query)
    if 'errors' in result:
        st.error(f"Error fetching views: {result['errors']}")
        return []
    
    # For now, we'll return teams as "views" since Linear's view structure is different
    teams = result.get('data', {}).get('viewer', {}).get('organization', {}).get('teams', {}).get('nodes', [])
    
    # Convert teams to a view-like structure
    views = []
    for team in teams:
        views.append({
            'id': team['id'],
            'name': f"Team: {team['name']}",
            'type': 'team'
        })
    
    return views

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

def get_issues_by_view(view_id):
    """Fetch issues by view ID"""
    query = """
    query IssuesByView($viewId: String!) {
        view(id: $viewId) {
            issues {
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
    }
    """
    
    result = make_linear_request(query, {'viewId': view_id})
    if 'errors' in result:
        st.error(f"Error fetching issues from view: {result['errors']}")
        return []
    
    return result.get('data', {}).get('view', {}).get('issues', {}).get('nodes', [])

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
    
    # Filter for release labels (assuming they follow a version pattern like X.Y.Z)
    import re
    release_pattern = re.compile(r'^\d+\.\d+\.\d+$')
    release_labels = [label for label in labels if release_pattern.match(label['name'])]
    
    # Sort by version number (newest first)
    def version_key(label):
        parts = label['name'].split('.')
        return [int(part) for part in parts]
    
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
    markdown = f"# 🚀 Release Notes - {release_version}\n\n"
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

def main():
    st.set_page_config(
        page_title="Linear Release Notes Generator",
        page_icon="🚀",
        layout="wide"
    )
    
    st.title("🚀 Linear Release Notes Generator")
    st.markdown("Generate beautiful release notes from your Linear issues and views.")
    
    # Check if API key is configured
    if not LINEAR_API_KEY:
        st.error("⚠️ LINEAR_API_KEY not found in environment variables. Please set it in your .env file.")
        st.code("LINEAR_API_KEY=your_api_key_here")
        return
    
    # Sidebar for configuration
    st.sidebar.header("Configuration")
    
    # Choose between label-based or view-based generation
    generation_method = st.sidebar.selectbox(
        "Generation Method",
        ["Release Label", "Linear View"]
    )
    
    if generation_method == "Release Label":
        # Label-based generation
        st.sidebar.subheader("Release Labels")
        
        # Fetch and display release labels
        with st.spinner("Fetching release labels..."):
            release_labels = get_release_labels()
        
        if release_labels:
            st.sidebar.success(f"Found {len(release_labels)} release labels")
            
            # Create a dropdown for release labels
            label_options = [label['name'] for label in release_labels]
            selected_label = st.sidebar.selectbox(
                "Choose a release label",
                ["Select a release label..."] + label_options,
                index=0
            )
            
            # Manual input option
            st.sidebar.markdown("---")
            st.sidebar.markdown("**Or enter a custom label:**")
            custom_label = st.sidebar.text_input(
                "Custom Release Label",
                placeholder="e.g., 106.5.0"
            )
            
            # Determine which label to use
            release_label = None
            if selected_label and selected_label != "Select a release label...":
                release_label = selected_label
            elif custom_label:
                release_label = custom_label
            
            if st.sidebar.button("Generate Release Notes", type="primary"):
                if not release_label:
                    st.error("Please select a release label or enter a custom one.")
                    return
                
                with st.spinner("Fetching issues..."):
                    issues = get_issues_by_label(release_label)
                
                if issues:
                    st.success(f"Found {len(issues)} issues for release {release_label}")
                    
                    # Generate and display release notes
                    release_notes = generate_release_notes(issues, release_label)
                    
                    # Display the markdown
                    st.subheader("Generated Release Notes")
                    st.markdown(release_notes)
                    
                    # Download button
                    st.download_button(
                        label="Download Release Notes",
                        data=release_notes,
                        file_name=f"changelog-{release_label}.md",
                        mime="text/markdown"
                    )
                    
                    # Notion Integration
                    if NOTION_AVAILABLE and os.getenv('NOTION_TOKEN'):
                        st.subheader("📝 Sync to Notion")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("Create New Notion Page", type="secondary"):
                                try:
                                    notion = NotionIntegration()
                                    database_id = st.session_state.get('selected_database_id')
                                    
                                    with st.spinner("Creating Notion page..."):
                                        page_id = notion.create_release_notes_page(
                                            release_version=release_label,
                                            markdown_content=release_notes,
                                            database_id=database_id
                                        )
                                    
                                    st.success(f"✅ Created Notion page! [View Page](https://notion.so/{page_id.replace('-', '')})")
                                    
                                except Exception as e:
                                    st.error(f"❌ Failed to create Notion page: {str(e)}")
                        
                        with col2:
                            if st.button("Update Existing Page", type="secondary"):
                                try:
                                    notion = NotionIntegration()
                                    database_id = st.session_state.get('selected_database_id')
                                    
                                    with st.spinner("Searching for existing page..."):
                                        existing_page_id = notion.find_existing_page(release_label, database_id)
                                    
                                    if existing_page_id:
                                        with st.spinner("Updating Notion page..."):
                                            notion.update_existing_page(existing_page_id, release_notes)
                                        st.success(f"✅ Updated existing Notion page! [View Page](https://notion.so/{existing_page_id.replace('-', '')})")
                                    else:
                                        st.warning("No existing page found for this release. Use 'Create New Notion Page' instead.")
                                        
                                except Exception as e:
                                    st.error(f"❌ Failed to update Notion page: {str(e)}")
                else:
                    st.warning(f"No issues found with label '{release_label}'")
        else:
            st.sidebar.warning("No release labels found. Please enter a custom label below.")
            
            # Manual input option
            custom_label = st.sidebar.text_input(
                "Release Label",
                placeholder="e.g., 106.5.0"
            )
            
            if st.sidebar.button("Generate Release Notes", type="primary"):
                if not custom_label:
                    st.error("Please enter a release label.")
                    return
                
                with st.spinner("Fetching issues..."):
                    issues = get_issues_by_label(custom_label)
                
                if issues:
                    st.success(f"Found {len(issues)} issues for release {custom_label}")
                    
                    # Generate and display release notes
                    release_notes = generate_release_notes(issues, custom_label)
                    
                    # Display the markdown
                    st.subheader("Generated Release Notes")
                    st.markdown(release_notes)
                    
                    # Download button
                    st.download_button(
                        label="Download Release Notes",
                        data=release_notes,
                        file_name=f"changelog-{custom_label}.md",
                        mime="text/markdown"
                    )
                    
                    # Notion Integration
                    if NOTION_AVAILABLE and os.getenv('NOTION_TOKEN'):
                        st.subheader("📝 Sync to Notion")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("Create New Notion Page", type="secondary"):
                                try:
                                    notion = NotionIntegration()
                                    database_id = st.session_state.get('selected_database_id')
                                    
                                    with st.spinner("Creating Notion page..."):
                                        page_id = notion.create_release_notes_page(
                                            release_version=custom_label,
                                            markdown_content=release_notes,
                                            database_id=database_id
                                        )
                                    
                                    st.success(f"✅ Created Notion page! [View Page](https://notion.so/{page_id.replace('-', '')})")
                                    
                                except Exception as e:
                                    st.error(f"❌ Failed to create Notion page: {str(e)}")
                        
                        with col2:
                            if st.button("Update Existing Page", type="secondary"):
                                try:
                                    notion = NotionIntegration()
                                    database_id = st.session_state.get('selected_database_id')
                                    
                                    with st.spinner("Searching for existing page..."):
                                        existing_page_id = notion.find_existing_page(custom_label, database_id)
                                    
                                    if existing_page_id:
                                        with st.spinner("Updating Notion page..."):
                                            notion.update_existing_page(existing_page_id, release_notes)
                                        st.success(f"✅ Updated existing Notion page! [View Page](https://notion.so/{existing_page_id.replace('-', '')})")
                                    else:
                                        st.warning("No existing page found for this release. Use 'Create New Notion Page' instead.")
                                        
                                except Exception as e:
                                    st.error(f"❌ Failed to update Notion page: {str(e)}")
                else:
                    st.warning(f"No issues found with label '{custom_label}'")
    
    else:
        # View-based generation
        st.sidebar.subheader("Select Linear View")
        
        with st.spinner("Fetching views..."):
            views = get_views()
        
        if views:
            view_options = {view['name']: view['id'] for view in views}
            selected_view_name = st.sidebar.selectbox("Choose a view", list(view_options.keys()))
            
            if selected_view_name:
                selected_view_id = view_options[selected_view_name]
                
                if st.sidebar.button("Generate Release Notes from View", type="primary"):
                    with st.spinner("Fetching issues from view..."):
                        issues = get_issues_by_view(selected_view_id)
                    
                    if issues:
                        st.success(f"Found {len(issues)} issues in view '{selected_view_name}'")
                        
                        # Generate and display release notes
                        release_notes = generate_release_notes(issues, f"View: {selected_view_name}")
                        
                        # Display the markdown
                        st.subheader("Generated Release Notes")
                        st.markdown(release_notes)
                        
                        # Download button
                        st.download_button(
                            label="Download Release Notes",
                            data=release_notes,
                            file_name=f"changelog-view-{selected_view_name.replace(' ', '-')}.md",
                            mime="text/markdown"
                        )
                        
                        # Notion Integration
                        if NOTION_AVAILABLE and os.getenv('NOTION_TOKEN'):
                            st.subheader("📝 Sync to Notion")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                if st.button("Create New Notion Page", type="secondary"):
                                    try:
                                        notion = NotionIntegration()
                                        database_id = st.session_state.get('selected_database_id')
                                        
                                        with st.spinner("Creating Notion page..."):
                                            page_id = notion.create_release_notes_page(
                                                release_version=f"View: {selected_view_name}",
                                                markdown_content=release_notes,
                                                database_id=database_id
                                            )
                                        
                                        st.success(f"✅ Created Notion page! [View Page](https://notion.so/{page_id.replace('-', '')})")
                                        
                                    except Exception as e:
                                        st.error(f"❌ Failed to create Notion page: {str(e)}")
                            
                            with col2:
                                if st.button("Update Existing Page", type="secondary"):
                                    try:
                                        notion = NotionIntegration()
                                        database_id = st.session_state.get('selected_database_id')
                                        
                                        with st.spinner("Searching for existing page..."):
                                            existing_page_id = notion.find_existing_page(f"View: {selected_view_name}", database_id)
                                        
                                        if existing_page_id:
                                            with st.spinner("Updating Notion page..."):
                                                notion.update_existing_page(existing_page_id, release_notes)
                                            st.success(f"✅ Updated existing Notion page! [View Page](https://notion.so/{existing_page_id.replace('-', '')})")
                                        else:
                                            st.warning("No existing page found for this release. Use 'Create New Notion Page' instead.")
                                            
                                    except Exception as e:
                                        st.error(f"❌ Failed to update Notion page: {str(e)}")
                    else:
                        st.warning(f"No issues found in view '{selected_view_name}'")
        else:
            st.error("No views found or error fetching views.")
    
    # Display recent activity
    st.sidebar.header("Recent Activity")
    st.sidebar.info("Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # Notion Integration Section
    if NOTION_AVAILABLE:
        st.sidebar.header("📝 Notion Integration")
        
        # Check if Notion is configured
        notion_token = os.getenv('NOTION_TOKEN')
        if notion_token:
            try:
                notion = NotionIntegration()
                st.sidebar.success("✅ Notion connected")
                
                # Get available databases
                databases = notion.get_databases()
                if databases:
                    st.sidebar.subheader("Available Databases")
                    database_options = {db.get('title', [{}])[0].get('plain_text', 'Untitled'): db['id'] for db in databases}
                    selected_database = st.sidebar.selectbox(
                        "Select Database",
                        ["Choose database..."] + list(database_options.keys())
                    )
                    
                    if selected_database and selected_database != "Choose database...":
                        st.session_state['selected_database_id'] = database_options[selected_database]
                
            except Exception as e:
                st.sidebar.error(f"❌ Notion connection failed: {str(e)}")
        else:
            st.sidebar.warning("⚠️ Notion not configured")
            st.sidebar.markdown("""
            To enable Notion integration, add to your `.env` file:
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
