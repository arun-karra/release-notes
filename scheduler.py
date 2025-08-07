#!/usr/bin/env python3
"""
Automated Release Notes Scheduler
This script runs the release notes generation automatically on a daily basis.
"""

import schedule
import time
import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

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

def get_recent_releases():
    """Get recent release labels (last 30 days)"""
    query = """
    query {
        labels(first: 100) {
            nodes {
                name
                createdAt
            }
        }
    }
    """
    
    result = make_linear_request(query)
    if 'errors' in result:
        logging.error(f"Error fetching labels: {result['errors']}")
        return []
    
    labels = result.get('data', {}).get('labels', {}).get('nodes', [])
    
    # Filter for release labels (assuming they follow a version pattern like X.Y.Z)
    import re
    release_pattern = re.compile(r'^\d+\.\d+\.\d+$')
    release_labels = [label['name'] for label in labels if release_pattern.match(label['name'])]
    
    return release_labels

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
        logging.error(f"Error fetching issues: {result['errors']}")
        return []
    
    return result.get('data', {}).get('issues', {}).get('nodes', [])

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

def save_release_notes(release_version, content):
    """Save release notes to file"""
    filename = f"changelog-{release_version}.md"
    
    # Create releases directory if it doesn't exist
    os.makedirs('releases', exist_ok=True)
    
    filepath = os.path.join('releases', filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logging.info(f"Release notes saved to {filepath}")
        return filepath
    except Exception as e:
        logging.error(f"Error saving release notes: {e}")
        return None

def generate_daily_release_notes():
    """Generate release notes for all recent releases"""
    logging.info("Starting daily release notes generation...")
    
    if not LINEAR_API_KEY:
        logging.error("LINEAR_API_KEY not found in environment variables")
        return
    
    try:
        # Get recent release labels
        release_labels = get_recent_releases()
        
        if not release_labels:
            logging.info("No release labels found")
            return
        
        logging.info(f"Found {len(release_labels)} release labels: {release_labels}")
        
        # Generate release notes for each release
        for release_label in release_labels:
            logging.info(f"Processing release {release_label}...")
            
            # Check if we already have recent release notes for this version
            filename = f"changelog-{release_label}.md"
            filepath = os.path.join('releases', filename)
            
            if os.path.exists(filepath):
                # Check if file was updated today
                file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_mtime.date() == datetime.now().date():
                    logging.info(f"Release notes for {release_label} already generated today, skipping...")
                    continue
            
            # Fetch issues for this release
            issues = get_issues_by_label(release_label)
            
            if issues:
                logging.info(f"Found {len(issues)} issues for release {release_label}")
                
                # Generate release notes
                release_notes = generate_release_notes(issues, release_label)
                
                # Save to file
                saved_path = save_release_notes(release_label, release_notes)
                
                if saved_path:
                    logging.info(f"Successfully generated release notes for {release_label}")
                else:
                    logging.error(f"Failed to save release notes for {release_label}")
            else:
                logging.info(f"No issues found for release {release_label}")
        
        logging.info("Daily release notes generation completed")
        
    except Exception as e:
        logging.error(f"Error during daily release notes generation: {e}")

def main():
    """Main function to run the scheduler"""
    parser = argparse.ArgumentParser(description='Release Notes Scheduler')
    parser.add_argument('--run-once', action='store_true', 
                       help='Run once and exit (useful for CI/CD)')
    
    args = parser.parse_args()
    
    logging.info("Starting Release Notes Scheduler...")
    
    if args.run_once:
        # Run once and exit
        logging.info("Running release notes generation once...")
        generate_daily_release_notes()
        logging.info("Completed single run.")
        return
    
    # Schedule the job to run daily at 9 AM
    schedule.every().day.at("09:00").do(generate_daily_release_notes)
    
    # Also run immediately on startup
    logging.info("Running initial release notes generation...")
    generate_daily_release_notes()
    
    logging.info("Scheduler started. Will run daily at 9:00 AM.")
    logging.info("Press Ctrl+C to stop the scheduler.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logging.info("Scheduler stopped by user")
    except Exception as e:
        logging.error(f"Scheduler error: {e}")

if __name__ == "__main__":
    main()
