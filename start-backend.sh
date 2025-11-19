#!/bin/bash

# Start the backend server
echo "🚀 Starting Reddit Insights Dashboard Backend..."
echo ""

cd "$(dirname "$0")/backend"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📚 Installing dependencies..."
pip install -q fastapi uvicorn pydantic praw tqdm python-dotenv openai

# Check for .env file
if [ ! -f "../.env" ]; then
    echo "⚠️  WARNING: .env file not found in parent directory"
    echo "   Please create it with your credentials before running pipelines"
    echo ""
fi

# Start server
echo "✅ Starting server on http://127.0.0.1:8000"
echo "   Press Ctrl+C to stop"
echo ""
uvicorn app:app --reload --host 0.0.0.0 --port 8000


