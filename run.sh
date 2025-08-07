#!/bin/bash

# Linear Release Notes Generator - Run Script

echo "🚀 Starting Linear Release Notes Generator..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "✅ Virtual environment found. Activating..."
    source venv/bin/activate
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating template..."
    cat > .env << EOF
# Linear API Configuration
# Get your API key from: https://linear.app/settings/api
LINEAR_API_KEY=your_linear_api_key_here

# Your Linear workspace URL (optional)
LINEAR_WORKSPACE_URL=https://linear.app/your-workspace
EOF
    echo "📝 Please edit .env file with your actual Linear API key before running the app."
fi

echo "🌐 Starting Streamlit application..."
echo "📱 The app will be available at: http://localhost:8501"
echo "🛑 Press Ctrl+C to stop the application"
echo ""

# Run the Streamlit app
streamlit run app.py
