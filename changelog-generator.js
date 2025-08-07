// Linear Changelog Generator
// This script pulls items from a specified release version label and formats them into user-friendly release notes

const axios = require('axios');
require('dotenv').config();
const fs = require('fs');
const path = require('path');
const os = require('os');

// Linear API configuration
const LINEAR_API_KEY = process.env.LINEAR_API_KEY;
const LINEAR_API_URL = 'https://api.linear.app/graphql';

// Your Linear workspace URL - CHANGE THIS to your workspace URL
const LINEAR_WORKSPACE_URL = 'https://linear.app/your-workspace';

// List of domain area labels to check for
const DOMAIN_AREAS = [
  "Activity",
  "Administration",
  "Assets",
  "End of Trial",
  "Forms",
  "Manage Area",
  "Media Player",
  "Notifications",
  "Permissions",
  "Reporting",
  "Study Events / Visit",
  "Study Procedures / Assessment",
  "Subjects",
  "Trial Configuration",
  "Uploader"
];

// Status emojis mapping
const STATUS_EMOJIS = {
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
};

// Statuses to exclude from the changelog
const EXCLUDED_STATUSES = ["Canceled", "Cancelled", "Duplicate"];

// Configuration for the changelog
const CHANGELOG_CONFIG = {
  // Release version label will be provided as command line argument
  releaseVersionLabel: process.argv[2],
  
  // Define which Linear labels map to which changelog categories
  categoryMappings: {
    "Bug": "🐛 Bug Fixes",
    "Feature": "✨ New Features", 
    "Improvement": "⚡ Improvements",
    "Documentation": "📚 Documentation",
    "Refactor": "🔧 Refactoring",
    "Performance": "🚀 Performance Improvements"
    // Add any other label-to-category mappings you need
  },
  
  // Default category for issues without a matching label
  defaultCategory: "Other Changes",
  
  // Release date (defaults to today)
  releaseDate: new Date().toISOString().split('T')[0] // Today's date in YYYY-MM-DD format
};

// GraphQL query to fetch issues with the specified release version label
// Modified to only include parent issues or standard issues (not sub-issues)
// Now also includes the state information
const query = `
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
`;

// Function to determine the category based on issue labels
function determineCategory(issue) {
  const issueLabels = issue.labels.nodes.map(label => label.name);
  
  // Try to find a matching category from our mappings
  for (const label of issueLabels) {
    if (CHANGELOG_CONFIG.categoryMappings[label]) {
      return CHANGELOG_CONFIG.categoryMappings[label];
    }
  }
  
  // Return default category if no match found
  return CHANGELOG_CONFIG.defaultCategory;
}

// Function to find domain area from issue labels
function findDomainArea(issue) {
  const issueLabels = issue.labels.nodes.map(label => label.name);
  
  // Find any matching domain area
  for (const label of issueLabels) {
    if (DOMAIN_AREAS.includes(label)) {
      return label;
    }
  }
  
  return null; // No domain area found
}

// Function to get status emoji for an issue
function getStatusEmoji(issue) {
  const stateName = issue.state.name;
  return STATUS_EMOJIS[stateName] || "";
}

// Function to check if an issue should be excluded
function shouldExcludeIssue(issue) {
  const stateName = issue.state.name;
  return EXCLUDED_STATUSES.includes(stateName);
}

// Function to get desktop path
function getDesktopPath() {
  return path.join(os.homedir(), 'Desktop');
}

// Function to sanitize filename
function sanitizeFilename(filename) {
  // Replace characters that are problematic in filenames
  return filename.replace(/[/\\?%*:|"<>]/g, '-');
}

// Function to save file to desktop
function saveToDesktop(filename, content) {
  const desktopPath = getDesktopPath();
  const filePath = path.join(desktopPath, filename);
  
  try {
    fs.writeFileSync(filePath, content);
    return filePath;
  } catch (error) {
    console.error(`Error saving file to desktop: ${error.message}`);
    return null;
  }
}

// Function to generate release notes
async function generateReleaseNotes() {
  try {
    if (!LINEAR_API_KEY) {
      throw new Error('LINEAR_API_KEY environment variable is not set');
    }
    
    if (!CHANGELOG_CONFIG.releaseVersionLabel) {
      throw new Error('Please provide a release version label as an argument, e.g., node changelog-generator.js "106.5.0"');
    }
    
    console.log(`Fetching issues for release: ${CHANGELOG_CONFIG.releaseVersionLabel}`);
    
    // Fetch issues from Linear
    const response = await axios.post(
      LINEAR_API_URL,
      { query, variables: { releaseLabel: CHANGELOG_CONFIG.releaseVersionLabel } },
      { headers: { 'Authorization': LINEAR_API_KEY } }
    );
    
    if (response.data.errors) {
      throw new Error(`GraphQL Error: ${JSON.stringify(response.data.errors)}`);
    }
    
    const issues = response.data.data.issues.nodes;
    
    if (issues.length === 0) {
      console.log(`No issues found with label "${CHANGELOG_CONFIG.releaseVersionLabel}"`);
      return;
    }
    
    console.log(`Found ${issues.length} issues for release ${CHANGELOG_CONFIG.releaseVersionLabel}`);
    
    // Filter out canceled and duplicate issues
    const filteredIssues = issues.filter(issue => !shouldExcludeIssue(issue));
    console.log(`After filtering: ${filteredIssues.length} issues (excluded ${issues.length - filteredIssues.length} canceled/duplicate issues)`);
    
    // Group issues by category
    const categorizedIssues = {};
    
    // Initialize categories with empty arrays
    Object.values(CHANGELOG_CONFIG.categoryMappings).forEach(category => {
      categorizedIssues[category] = [];
    });
    categorizedIssues[CHANGELOG_CONFIG.defaultCategory] = [];
    
    // Categorize issues
    filteredIssues.forEach(issue => {
      const category = determineCategory(issue);
      const domainArea = findDomainArea(issue);
      const statusEmoji = getStatusEmoji(issue);
      
      categorizedIssues[category].push({
        title: issue.title,
        identifier: issue.identifier,
        url: issue.url || `${LINEAR_WORKSPACE_URL}/issue/${issue.identifier}`,
        domainArea: domainArea,
        statusEmoji: statusEmoji
      });
    });
    
    
// Generate markdown for the release notes
let markdown = `# 🚀 Release Notes - ${CHANGELOG_CONFIG.releaseVersionLabel}

`;
    
    // Add issues by category
    Object.entries(categorizedIssues).forEach(([category, issues]) => {
      if (issues.length > 0) {
        markdown += `## ${category}\n\n`;
        
        issues.forEach(issue => {
          markdown += `- ${issue.statusEmoji} **${issue.title}** ([${issue.identifier}](${issue.url}))`;
          if (issue.domainArea) {
            markdown += ` [${issue.domainArea}]`;
          }
          markdown += `\n`;
        });
        
        markdown += '\n';
      }
    });
    
    console.log(markdown);
    
    // Sanitize the filename
    const sanitizedVersionLabel = sanitizeFilename(CHANGELOG_CONFIG.releaseVersionLabel);
    const fileName = `changelog-${sanitizedVersionLabel}.md`;
    
    // Save to current directory
    fs.writeFileSync(fileName, markdown);
    console.log(`\nChangelog written to ${fileName} in current directory`);
    
    // Save to desktop
    const desktopPath = saveToDesktop(fileName, markdown);
    if (desktopPath) {
      console.log(`Changelog also saved to your desktop at: ${desktopPath}`);
    }
    
  } catch (error) {
    console.error('Error generating release notes:', error.message);
    if (error.response) {
      console.error('API response:', error.response.data);
    }
  }
}

// Execute the script
generateReleaseNotes();
