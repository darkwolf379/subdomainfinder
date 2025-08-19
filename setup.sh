#!/bin/bash

# Advanced Subdomain Monitor - Quick Setup Script

echo "🚀 Setting up Advanced Subdomain Monitor..."

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "⬇️ Installing dependencies..."
pip install --upgrade pip
pip install aiohttp dnspython

echo "✅ Setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Set your Telegram bot token:"
echo "   export TELEGRAM_BOT_TOKEN='your_bot_token_here'"
echo ""
echo "2. Set your Telegram chat ID:"
echo "   export TELEGRAM_CHAT_ID='your_chat_id_here'"
echo ""
echo "3. Run the application:"
echo "   python main.py --mode interactive"
echo ""
echo "🔗 For detailed setup instructions, see README.md"
