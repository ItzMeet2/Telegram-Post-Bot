# Manhwa Posting Bot

A comprehensive Telegram bot for posting manhwa content to channels with advanced features.

## Features
- 📝 **Text & Photo Posts** - Rich formatting preserved
- 🖼️ **Photo Posts** - Images with captions
- 🔗 **URL Buttons** - Add clickable links to posts
- 🔔 **Notification Control** - Toggle notifications on/off
- 📢 **Multi-Channel Support** - @Manhwa_Digest and @Ongoing_Manhwas
- 🚀 **Batch Posting** - Post to both channels simultaneously
- 👁️ **Content Preview** - Review before publishing
- ✏️ **Edit & Delete** - Modify content before posting

## Bot Configuration
- **Bot Token**: `8410264334:AAFdvMbhmq4vz_a8LorZsTIQFJA3Bkpyzyw`
- **Target Channels**: @Manhwa_Digest, @Ongoing_Manhwas
- **Default URL Button**: "Read 📜"

## Commands
- `/start` - Open main menu with all options
- `/post` - Create and post content directly
- `/channels` - Manage channel settings
- `/help` - Show detailed help and usage

## Usage
1. Start bot with `/start` or any command
2. Choose content type (Text/Photo)
3. Add content and optional URL buttons
4. Preview and edit if needed
5. Select target channels
6. Publish instantly

## Local Setup
1. Install dependencies: `pip install pyTelegramBotAPI`
2. Run: `python main.py`
3. Keep terminal open for 24/7 operation

## Deployment on Render
1. Push this repo to GitHub
2. Connect to Render.com
3. Deploy as Web Service
4. Bot runs 24/7 for 750 hours/month (FREE)

## File Structure
- `main.py` - Main bot logic and handlers
- `config.py` - Bot token and channel configuration
- `requirements.txt` - Python dependencies
- `README.md` - Documentation