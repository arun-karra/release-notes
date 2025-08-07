# 🚀 Linear Release Notes Generator

A modern, web-based release notes generator that pulls data from Linear and provides a beautiful frontend interface. Features automated daily updates, Linear views integration, and cloud hosting capabilities.

## ✨ Features

- **🌐 Web Frontend**: Beautiful Streamlit-based interface accessible from anywhere
- **📊 Linear Views Integration**: Generate release notes from any Linear view, not just labels
- **🤖 Automated Updates**: Daily automatic generation and updates via GitHub Actions
- **📁 Cloud Hosting**: Deploy to Streamlit Cloud for easy access
- **🎨 Modern UI**: Clean, responsive interface with real-time updates
- **📥 Download Support**: Export release notes as Markdown files
- **🔍 Smart Filtering**: Automatic categorization and domain area detection

## 🚀 Quick Start

### Prerequisites

1. **Linear API Key**: Get your API key from [Linear Settings](https://linear.app/settings/api)
2. **Python 3.9+**: Required for running the application
3. **GitHub Account**: For hosting and automated updates

### Local Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/cp_release_notes.git
   cd cp_release_notes
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   Create a `.env` file in the root directory:
   ```env
   LINEAR_API_KEY=your_linear_api_key_here
   LINEAR_WORKSPACE_URL=https://linear.app/your-workspace
   ```

4. **Run the web application**:
   ```bash
   streamlit run app.py
   ```

5. **Open your browser** and navigate to `http://localhost:8501`

## 🌐 Web Interface

The Streamlit web interface provides:

- **Release Label Generation**: Generate release notes from specific version labels
- **Linear Views Integration**: Select from your Linear views to generate release notes
- **Real-time Preview**: See generated release notes instantly
- **Download Functionality**: Export release notes as Markdown files
- **Responsive Design**: Works on desktop and mobile devices

### Using the Web Interface

1. **Choose Generation Method**:
   - **Release Label**: Enter a specific version label (e.g., "106.5.0")
   - **Linear View**: Select from your existing Linear views

2. **Generate Release Notes**:
   - Click the "Generate Release Notes" button
   - Wait for the system to fetch and process issues
   - Review the generated release notes

3. **Download Results**:
   - Use the download button to save release notes as Markdown files

## 🤖 Automated Updates

### GitHub Actions Setup

1. **Fork this repository** to your GitHub account

2. **Add secrets** to your repository:
   - Go to Settings → Secrets and variables → Actions
   - Add the following secrets:
     - `LINEAR_API_KEY`: Your Linear API key
     - `LINEAR_WORKSPACE_URL`: Your Linear workspace URL
     - `STREAMLIT_SHARING_TOKEN`: Your Streamlit sharing token (optional)

3. **Enable GitHub Actions**:
   - The workflow will automatically run daily at 9 AM UTC
   - Manual triggers are also available via the Actions tab

### Local Scheduler

For local automated updates:

```bash
# Run the scheduler (runs daily at 9 AM)
python scheduler.py

# Run once and exit (useful for testing)
python scheduler.py --run-once
```

## 📊 Linear Views Integration

The application now supports generating release notes from Linear views:

1. **View Selection**: Choose from your existing Linear views
2. **Automatic Processing**: Issues are automatically categorized and formatted
3. **Flexible Filtering**: Use any view criteria you've set up in Linear

### Supported View Types

- **Backlog Views**: Generate release notes from backlog items
- **Sprint Views**: Create release notes from sprint contents
- **Custom Views**: Use any custom view you've created
- **Filtered Views**: Apply your own filtering criteria

## 🎨 Release Notes Format

Generated release notes include:

- **Categorized Sections**: Bug fixes, features, improvements, etc.
- **Status Indicators**: Visual emojis showing issue status
- **Domain Areas**: Automatic detection and labeling
- **Issue Links**: Direct links to Linear issues
- **Timestamps**: Generation date and time

### Example Output

```markdown
# 🚀 Release Notes - 106.5.0

*Generated on 2024-01-15 09:00:00*

## ✨ New Features

- ✅ **Add user authentication** ([ABC-123](https://linear.app/issue/ABC-123)) [Permissions]
- ✅ **Implement dark mode** ([ABC-124](https://linear.app/issue/ABC-124)) [UI/UX]

## 🐛 Bug Fixes

- ✅ **Fix login redirect issue** ([ABC-125](https://linear.app/issue/ABC-125)) [Authentication]
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `LINEAR_API_KEY` | Your Linear API key | Yes |
| `LINEAR_WORKSPACE_URL` | Your Linear workspace URL | No (defaults to placeholder) |

### Customization

You can customize the application by modifying:

- **Category Mappings**: Edit `CATEGORY_MAPPINGS` in `app.py`
- **Domain Areas**: Update `DOMAIN_AREAS` list
- **Status Emojis**: Modify `STATUS_EMOJIS` dictionary
- **Excluded Statuses**: Update `EXCLUDED_STATUSES` list

## 🚀 Deployment

### Streamlit Cloud Deployment

1. **Push to GitHub**: Ensure your code is in a GitHub repository

2. **Connect to Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub account
   - Select your repository
   - Deploy the application

3. **Configure Environment Variables**:
   - Add your Linear API key and workspace URL in Streamlit Cloud settings

### Alternative Deployment Options

- **Heroku**: Use the provided `Procfile` and `runtime.txt`
- **Docker**: Build and run the Docker container
- **Local Server**: Run on your own server with `streamlit run app.py`

## 📁 Project Structure

```
cp_release_notes/
├── app.py                 # Streamlit web application
├── scheduler.py           # Automated update scheduler
├── changelog-generator.js # Original Node.js script
├── requirements.txt       # Python dependencies
├── package.json          # Node.js dependencies
├── .github/
│   └── workflows/
│       └── deploy.yml    # GitHub Actions workflow
├── releases/             # Generated release notes (auto-created)
└── README.md            # This file
```

## 🔍 Troubleshooting

### Common Issues

1. **API Key Issues**:
   - Ensure your Linear API key is correct
   - Check that the key has the necessary permissions

2. **No Issues Found**:
   - Verify the release label exists in Linear
   - Check that issues are properly labeled
   - Ensure issues are not in excluded statuses

3. **View Access Issues**:
   - Confirm you have access to the selected view
   - Check view permissions in Linear

4. **Deployment Issues**:
   - Verify environment variables are set correctly
   - Check GitHub Actions logs for errors
   - Ensure repository secrets are configured

### Getting Help

- **Issues**: Create an issue on GitHub
- **Documentation**: Check the Linear API documentation
- **Community**: Join the Streamlit community for support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the ISC License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Linear](https://linear.app) for the excellent API
- [Streamlit](https://streamlit.io) for the web framework
- [GitHub Actions](https://github.com/features/actions) for automation

---

**Happy Release Note Generating! 🚀**
