#!/bin/bash
# setup-vercel.sh - Quick setup script for Vercel deployment

echo "================================"
echo "FatigueGuard Pro - Vercel Setup"
echo "================================"
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "⚠️  ngrok not found. Installing..."
    # Note: ngrok needs to be installed separately from their website
    echo "📥 Please install ngrok from: https://ngrok.com/download"
    echo "   Then run: npm install -g pyngrok"
    exit 1
fi

echo "✅ ngrok found!"
echo ""

# Start ngrok with backend
echo "🚀 Starting backend with ngrok tunnel..."
echo ""

cd backend
python run_with_ngrok.py

echo ""
echo "📋 Next steps:"
echo "1. Copy the ngrok URL from above"
echo "2. Go to Vercel Dashboard → Your Project → Settings → Environment Variables"
echo "3. Set REACT_APP_API_URL to the ngrok URL"
echo "4. Push to GitHub to trigger Vercel redeploy"
echo "5. Your Vercel app will now connect to your local backend!"
