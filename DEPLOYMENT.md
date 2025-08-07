# 🚀 Deployment Guide

## Environment Variables Setup

Since `.env` files are excluded from git for security reasons, you'll need to configure environment variables in your deployment platform.

### For Streamlit Cloud Deployment

1. **Go to Streamlit Cloud**: [https://share.streamlit.io](https://share.streamlit.io)
2. **Connect your GitHub repository**: `arun-karra/release-notes`
3. **Deploy the app**: Set main file to `app.py`
4. **Configure Environment Variables**:
   - Go to your app's settings in Streamlit Cloud
   - Find the "Secrets" section
   - Add the following configuration:

```toml
# Add this to your Streamlit Cloud secrets
LINEAR_API_KEY = "your_linear_api_key_here"
LINEAR_WORKSPACE_URL = "https://linear.app/your-workspace"

# Notion Integration
NOTION_TOKEN = "your_notion_integration_token_here"
NOTION_DATABASE_ID = "your_notion_database_id_here"
NOTION_PARENT_PAGE_ID = "your_notion_parent_page_id_here"
```

### For Local Development

Your local `.env` file should contain:

```env
LINEAR_API_KEY=your_linear_api_key_here
LINEAR_WORKSPACE_URL=https://linear.app/your-workspace

# Notion Integration
NOTION_TOKEN=your_notion_integration_token_here
NOTION_DATABASE_ID=your_notion_database_id_here
NOTION_PARENT_PAGE_ID=your_notion_parent_page_id_here
```

## Security Best Practices

✅ **Do NOT commit .env files to git** (already configured in .gitignore)
✅ **Use deployment platform secrets** for production
✅ **Keep local .env for development** only
✅ **Rotate API keys regularly**

## Testing Deployment

1. **Local test**: `streamlit run app.py`
2. **Cloud deployment**: Visit your Streamlit Cloud URL
3. **Test Notion integration**: Generate release notes and sync to Notion

## Troubleshooting

- **Notion not working**: Check that you've shared your database/page with the integration
- **Linear not working**: Verify your API key has the correct permissions
- **Environment variables not loading**: Restart your Streamlit app after adding secrets
