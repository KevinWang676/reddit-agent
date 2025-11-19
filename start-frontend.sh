#!/bin/bash

# Start the frontend development server
echo "🚀 Starting Reddit Insights Dashboard Frontend..."
echo ""

cd "$(dirname "$0")/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    echo ""
fi

# Start dev server
echo "✅ Starting development server..."
echo "   The dashboard will open automatically"
echo "   Press Ctrl+C to stop"
echo ""
npm run dev


