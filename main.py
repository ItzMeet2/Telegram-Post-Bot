import telebot
from telebot import types
import os
from flask import Flask
import threading
import time
import requests

# Bot Configuration
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8410264334:AAFdvMbhmq4vz_a8LorZsTIQFJA3Bkpyzyw')
CHANNELS = {
    'Manhwa_Digest': '@Manhwa_Digest',
    'Ongoing_Manhwas': '@Ongoing_Manhwas'
}

bot = telebot.TeleBot(BOT_TOKEN)
user_states = {}
user_data = {}

# Admin check function
def is_admin(user_id):
    """Check if user is admin in any of the target channels"""
    for channel in CHANNELS.values():
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status in ['creator', 'administrator']:
                return True
        except Exception:
            continue
    return False

def admin_required(func):
    """Decorator to check admin access"""
    def wrapper(message_or_call):
        user_id = message_or_call.from_user.id
        if not is_admin(user_id):
            error_text = """
🚫 **ACCESS DENIED**

❌ **You are not authorized to use this bot.**

🔐 **Admin Access Required:**
• You must be an admin in @Manhwa_Digest or @Ongoing_Manhwas
• Contact the channel owner for access

👤 **Your ID:** `{}`
""".format(user_id)
            
            if hasattr(message_or_call, 'message'):
                # It's a callback query
                bot.edit_message_text(error_text, message_or_call.message.chat.id, message_or_call.message.message_id, parse_mode='Markdown')
            else:
                # It's a message
                bot.reply_to(message_or_call, error_text, parse_mode='Markdown')
            return
        return func(message_or_call)
    return wrapper

@bot.message_handler(commands=['start'])
@admin_required
def start_command(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📝 Create Post", callback_data="create_post"),
        types.InlineKeyboardButton("⏰ Schedule", callback_data="scheduled_post")
    )
    markup.add(
        types.InlineKeyboardButton("✏️ Edit Post", callback_data="edit_post"),
        types.InlineKeyboardButton("📊 Status", callback_data="channel_status")
    )
    markup.add(types.InlineKeyboardButton("⚙️ Settings", callback_data="settings"))
    
    welcome_text = """
🎆 **MANHWA POSTING BOT** 🎆

📚 Welcome to your Manhwa content manager!

✨ **Quick Actions:**
• Create and post content instantly
• Schedule posts for later
• Monitor channel status
• Manage bot settings

👇 **Choose an option below:**
"""
    
    bot.reply_to(message, welcome_text, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data in ['create_post', 'scheduled_post', 'edit_post', 'channel_status', 'settings', 'global_cancel'])
@admin_required
def main_menu_callback(call):
    if call.data == 'global_cancel':
        user_id = call.from_user.id
        if user_id in user_data:
            del user_data[user_id]
        if user_id in user_states:
            del user_states[user_id]
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_menu"))
        bot.edit_message_text("❌ **ALL CANCELLED**\n\n✅ All content and settings have been cleared.\n\nYou can start fresh from the main menu.", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')
        return
    
    if call.data == 'create_post':
        create_post_menu(call)
    elif call.data == 'scheduled_post':
        coming_soon_text = """
⏰ **SCHEDULED POSTING**

🚀 **Coming Soon!**

📊 **Planned Features:**
• Schedule posts for specific times
• Recurring post automation
• Time zone support
• Queue management

🛠️ Currently in development...
"""
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_menu"))
        bot.edit_message_text(coming_soon_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')
    elif call.data == 'edit_post':
        # Check if user has any content to edit
        user_id = call.from_user.id
        if user_id in user_data and user_data[user_id]:
            # User has content, show edit options
            data = user_data[user_id]
            if 'message_text' in data:
                # Show current text for editing
                edit_text = f"""
✏️ **EDIT TEXT POST**

📝 **Current message:**
{data['message_text'][:300]}{'...' if len(data['message_text']) > 300 else ''}

✏️ **Send your updated message below:**
"""
                user_states[user_id] = 'post_text'
                bot.edit_message_text(edit_text, call.message.chat.id, call.message.message_id, parse_mode='Markdown')
            else:
                # Show photo caption editing options
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("✏️ Edit Caption", callback_data="edit_caption"),
                    types.InlineKeyboardButton("🖼️ New Photo", callback_data="new_photo")
                )
                markup.add(types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_menu"))
                
                edit_text = f"""
✏️ **EDIT PHOTO POST**

🖼️ **Current caption:**
{data.get('caption', 'No caption')[:300]}{'...' if len(data.get('caption', '')) > 300 else ''}

🎯 **Choose what to edit:**
"""
                bot.edit_message_text(edit_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')
        else:
            # No content to edit, show message
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("📝 Create New Post", callback_data="create_post"),
                types.InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")
            )
            
            no_content_text = """
✏️ **EDIT POST**

📋 **No content to edit**

You don't have any draft content to edit.
Create a new post first, then you can edit it.

📝 **What would you like to do?**
"""
            bot.edit_message_text(no_content_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')
    elif call.data == 'channel_status':
        show_channel_status(call)
    elif call.data == 'settings':
        show_settings(call)

def create_post_menu(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📝 Text Post", callback_data="post_text"),
        types.InlineKeyboardButton("🖼️ Photo Post", callback_data="post_photo")
    )
    markup.add(
        types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_menu"),
        types.InlineKeyboardButton("❌ Cancel All", callback_data="global_cancel")
    )
    
    create_text = """
📝 **CREATE NEW POST**

🎯 Choose your content type:

📝 **Text Post** - Share manhwa updates, reviews, or announcements
🖼️ **Photo Post** - Upload images with captions

✨ All formatting and emojis will be preserved!
"""
    
    bot.edit_message_text(create_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')

def show_channel_status(call):
    status_text = """
📊 **CHANNEL STATUS MONITOR**

🔍 **Checking channel connectivity...**

"""
    
    for name, channel in CHANNELS.items():
        try:
            chat = bot.get_chat(channel)
            member_count = bot.get_chat_member_count(channel)
            status_text += f"✅ **{name}**\n   • Channel: {channel}\n   • Members: {member_count:,}\n   • Status: 🟢 Connected\n\n"
        except Exception as e:
            status_text += f"❌ **{name}**\n   • Channel: {channel}\n   • Status: 🔴 No Access\n   • Error: Bot not admin\n\n"
    
    status_text += "ℹ️ Make sure bot is admin in all channels"
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("🔄 Refresh Status", callback_data="channel_status"))
    markup.add(
        types.InlineKeyboardButton("🔙 Back to Channels", callback_data="back_to_channels"),
        types.InlineKeyboardButton("🔙 Main Menu", callback_data="back_to_menu")
    )
    markup.add(types.InlineKeyboardButton("❌ Cancel All", callback_data="global_cancel"))
    bot.edit_message_text(status_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')

def show_settings(call):
    settings_text = """
⚙️ **BOT SETTINGS & INFO**

📢 **Target Channels:**
• 📚 **Manhwa Digest**
   → @Manhwa_Digest
   → Main content channel

• 🔄 **Ongoing Manhwas**
   → @Ongoing_Manhwas
   → Updates & releases

🤖 **Bot Information:**
• Status: 🟢 Active & Running
• Version: 2.0
• Features: Text, Photo, Multi-channel
• Hosting: Render (750h/month)

📊 **Usage Stats:**
• Posts sent today: 0
• Uptime: 100%
"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_menu"),
        types.InlineKeyboardButton("❌ Cancel All", callback_data="global_cancel")
    )
    bot.edit_message_text(settings_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data in ['post_text', 'post_photo', 'back_to_menu', 'global_cancel', 'view_channels', 'add_channel', 'remove_channel', 'back_to_channels'])
@admin_required
def post_type_callback(call):
    if call.data == 'global_cancel':
        user_id = call.from_user.id
        if user_id in user_data:
            del user_data[user_id]
        if user_id in user_states:
            del user_states[user_id]
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_menu"))
        bot.edit_message_text("❌ **ALL CANCELLED**\n\n✅ All content and settings have been cleared.\n\nYou can start fresh from the main menu.", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')
        return
    
    elif call.data == 'view_channels':
        show_channel_status(call)
    
    elif call.data == 'add_channel':
        bot.edit_message_text("➕ **ADD CHANNEL**\n\n🚀 **Coming Soon!**\n\nThis feature will allow you to add new channels to your bot.", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back to Channels", callback_data="back_to_channels"))
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == 'remove_channel':
        bot.edit_message_text("➖ **REMOVE CHANNEL**\n\n🚀 **Coming Soon!**\n\nThis feature will allow you to remove channels from your bot.", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back to Channels", callback_data="back_to_channels"))
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == 'back_to_channels':
        show_channel_management_inline(call)
    
    elif call.data == 'back_to_menu':
        start_command_inline(call)
    else:
        user_states[call.from_user.id] = call.data
        if call.data == 'post_text':
            text_prompt = """
📝 **TEXT POST COMPOSER**

✏️ **Send your message below:**

✨ **Tips:**
• All emojis and formatting will be preserved
• Use **bold** and *italic* text
• Special characters like ⟨⟨ ⟩⟩ work perfectly
• Line breaks and spacing maintained

💬 Type your message now...
"""
            bot.edit_message_text(text_prompt, call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        else:
            photo_prompt = """
🖼️ **PHOTO POST COMPOSER**

📷 **Send your photo below:**

✨ **Tips:**
• Add a caption for context
• High-quality images work best
• Captions support formatting
• Multiple photos? Send them one by one

🖼️ Upload your image now...
"""
            bot.edit_message_text(photo_prompt, call.message.chat.id, call.message.message_id, parse_mode='Markdown')

def start_command_inline(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📝 Create Post", callback_data="create_post"),
        types.InlineKeyboardButton("⏰ Schedule", callback_data="scheduled_post")
    )
    markup.add(
        types.InlineKeyboardButton("✏️ Edit Post", callback_data="edit_post"),
        types.InlineKeyboardButton("📊 Status", callback_data="channel_status")
    )
    markup.add(types.InlineKeyboardButton("⚙️ Settings", callback_data="settings"))
    
    welcome_text = """
🎆 **MANHWA POSTING BOT** 🎆

📚 Welcome to your Manhwa content manager!

✨ **Quick Actions:**
• Create and post content instantly
• Schedule posts for later
• Monitor channel status
• Manage bot settings

👇 **Choose an option below:**
"""
    
    bot.edit_message_text(welcome_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(commands=['post'])
@admin_required
def post_command(message):
    # Trigger the create_post callback
    create_post_menu_inline(message)

@bot.message_handler(commands=['channels'])
@admin_required
def channels_command(message):
    # Trigger the channel management
    show_channel_management_message(message)

@bot.message_handler(commands=['help'])
@admin_required
def help_command(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_menu"))
    
    help_text = """
🤖 **MANHWA BOT COMMANDS**

📝 **Main Commands:**
/start - Open main menu
/post - Create and post content
/channels - Manage channels
/help - Show this help

🎯 **Quick Actions:**
• Send /post to create content instantly
• Send /channels to manage your channels
• Use buttons for easy navigation

🚀 **Features:**
• Text and photo posting
• URL buttons with links
• Notification controls
• Multi-channel support

📚 **Usage:**
1. Use /post to create content
2. Add text, photos, or URLs
3. Select target channels
4. Publish instantly!
"""
    
    bot.reply_to(message, help_text, reply_markup=markup, parse_mode='Markdown')

def create_post_menu_inline(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📝 Text Post", callback_data="post_text"),
        types.InlineKeyboardButton("🖼️ Photo Post", callback_data="post_photo")
    )
    markup.add(
        types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_menu"),
        types.InlineKeyboardButton("❌ Cancel All", callback_data="global_cancel")
    )
    
    create_text = """
📝 **CREATE NEW POST**

🎯 Choose your content type:

📝 **Text Post** - Share manhwa updates, reviews, or announcements
🖼️ **Photo Post** - Upload images with captions

✨ All formatting and emojis will be preserved!
"""
    
    bot.reply_to(message, create_text, reply_markup=markup, parse_mode='Markdown')

def show_channel_management_message(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 View Channels", callback_data="view_channels"),
        types.InlineKeyboardButton("➕ Add Channel", callback_data="add_channel")
    )
    markup.add(
        types.InlineKeyboardButton("➖ Remove Channel", callback_data="remove_channel"),
        types.InlineKeyboardButton("🔄 Refresh Status", callback_data="channel_status")
    )
    markup.add(
        types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_menu"),
        types.InlineKeyboardButton("❌ Cancel", callback_data="global_cancel")
    )
    
    channel_text = """
📢 **CHANNEL MANAGEMENT**

📊 **Current Channels:**
"""
    
    for name, channel in CHANNELS.items():
        channel_text += f"• **{name}**: {channel}\n"
    
    channel_text += "\n🎯 **Choose an action:**"
    
    bot.reply_to(message, channel_text, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(content_types=['text'])
@admin_required
def handle_text(message):
    user_id = message.from_user.id
    if user_id in user_states:
        if user_states[user_id] == 'post_text':
            user_data[user_id] = {
                'message_text': message.text,
                'message_entities': message.entities
            }
            show_preview(message, 'text')
            del user_states[user_id]
        elif user_states[user_id] == 'edit_caption_text':
            # Update only the caption, keep the photo
            if user_id in user_data:
                user_data[user_id]['caption'] = message.text
                user_data[user_id]['caption_entities'] = message.entities
            
            # Show success message with options
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("👁️ Preview", callback_data="preview_content"),
                types.InlineKeyboardButton("✏️ Edit More", callback_data="edit_content")
            )
            markup.add(
                types.InlineKeyboardButton("🚀 Send", callback_data="proceed_to_channels"),
                types.InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")
            )
            
            success_text = f"""
✅ **CAPTION UPDATED!**

💬 **New caption:**
{message.text[:200]}{'...' if len(message.text) > 200 else ''}

🎯 **Choose next action:**
"""
            
            bot.reply_to(message, success_text, reply_markup=markup, parse_mode='Markdown')
            del user_states[user_id]
        elif user_states[user_id] == 'add_url_button':
            # Extract URL from any text (including Telegram forwarded links)
            import re
            
            try:
                text = message.text.strip()
                
                # Multiple URL patterns to catch different formats
                url_patterns = [
                    r'https?://[^\s]+',  # Standard http/https URLs
                    r't\.me/[^\s]+',      # Telegram t.me links
                    r'www\.[^\s]+',      # www links
                ]
                
                url = None
                
                # Try each pattern
                for pattern in url_patterns:
                    urls = re.findall(pattern, text)
                    if urls:
                        url = urls[0]
                        # Add https:// if missing
                        if not url.startswith(('http://', 'https://')):
                            url = 'https://' + url
                        break
                
                # Fallback: check if the entire text looks like a URL
                if not url:
                    if ('.' in text and 
                        (' ' not in text or text.count(' ') <= 1) and 
                        len(text) > 4):
                        url = text if text.startswith(('http://', 'https://')) else 'https://' + text
                
                if url:
                    if user_id in user_data:
                        if 'url_buttons' not in user_data[user_id]:
                            user_data[user_id]['url_buttons'] = []
                        user_data[user_id]['url_buttons'].append({'text': 'Read 📜', 'url': url})
                    
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton("🔙 Back to Preview", callback_data="back_to_preview"))
                    
                    # Clean URL for display (remove any problematic characters)
                    clean_url = url.replace('*', '').replace('_', '').replace('`', '')
                    bot.reply_to(message, f"✅ URL BUTTON ADDED!\n\nButton: Read 📜\nURL: {clean_url}\n\nButton will appear below your post.", reply_markup=markup)
                else:
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton("🔙 Back to Preview", callback_data="back_to_preview"))
                    bot.reply_to(message, f"❌ No URL Found!\n\nYour text: {text[:50]}...\n\nPlease send a valid URL or link.", reply_markup=markup)
            except Exception as e:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("🔙 Back to Preview", callback_data="back_to_preview"))
                bot.reply_to(message, "❌ Error processing URL!\n\nPlease try sending just the URL without any extra text.", reply_markup=markup)
            
            del user_states[user_id]

@bot.message_handler(content_types=['photo'])
@admin_required
def handle_photo(message):
    user_id = message.from_user.id
    if user_id in user_states and user_states[user_id] == 'post_photo':
        user_data[user_id] = {
            'photo_file_id': message.photo[-1].file_id,
            'caption': message.caption or "",
            'caption_entities': message.caption_entities
        }
        show_preview(message, 'photo')
        del user_states[user_id]

def show_preview(message, content_type):
    user_id = message.from_user.id
    data = user_data.get(user_id, {})
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✏️ Edit", callback_data="edit_content"),
        types.InlineKeyboardButton("🗑️ Delete", callback_data="delete_content")
    )
    markup.add(
        types.InlineKeyboardButton("👁️ Preview", callback_data="preview_content"),
        types.InlineKeyboardButton("🚀 Send", callback_data="proceed_to_channels")
    )
    markup.add(
        types.InlineKeyboardButton("🔗 Add URL Button", callback_data="add_url_button"),
        types.InlineKeyboardButton("🔔 Notification", callback_data="toggle_notification")
    )
    markup.add(
        types.InlineKeyboardButton("❌ Cancel All", callback_data="cancel_all"),
        types.InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")
    )
    
    if content_type == 'text':
        preview_text = f"""
📝 **CONTENT PREVIEW**

✨ **Your message:**
{data.get('message_text', '')[:200]}{'...' if len(data.get('message_text', '')) > 200 else ''}

🎯 **Choose an action:**
"""
        bot.reply_to(message, preview_text, reply_markup=markup, parse_mode='Markdown')
    else:
        caption_preview = data.get('caption', 'No caption')
        preview_text = f"""
🖼️ **PHOTO PREVIEW**

📷 **Photo uploaded successfully!**
💬 **Caption:** {caption_preview[:100]}{'...' if len(caption_preview) > 100 else ''}

🎯 **Choose an action:**
"""
        bot.reply_to(message, preview_text, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data in ['edit_content', 'delete_content', 'preview_content', 'proceed_to_channels', 'back_to_preview', 'edit_caption', 'new_photo', 'save_caption', 'add_url_button', 'toggle_notification', 'notification_on', 'notification_off', 'cancel_all', 'global_cancel', 'view_channels', 'add_channel', 'remove_channel', 'back_to_channels'])
@admin_required
def content_action_callback(call):
    user_id = call.from_user.id
    
    if call.data == 'global_cancel':
        if user_id in user_data:
            del user_data[user_id]
        if user_id in user_states:
            del user_states[user_id]
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_menu"))
        bot.edit_message_text("❌ **ALL CANCELLED**\n\n✅ All content and settings have been cleared.\n\nYou can start fresh from the main menu.", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')
        return
    
    if call.data == 'edit_content':
        if user_id in user_data:
            data = user_data[user_id]
            if 'message_text' in data:
                # Show current text for editing
                edit_text = f"""
✏️ **EDIT TEXT POST**

📝 **Current message:**
{data['message_text']}

✏️ **Send your updated message below:**
"""
                user_states[user_id] = 'post_text'
                bot.edit_message_text(edit_text, call.message.chat.id, call.message.message_id, parse_mode='Markdown')
            else:
                # Show caption editing options
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("✏️ Edit Caption", callback_data="edit_caption"),
                    types.InlineKeyboardButton("🖼️ New Photo", callback_data="new_photo")
                )
                markup.add(types.InlineKeyboardButton("🔙 Back to Preview", callback_data="back_to_preview"))
                
                edit_text = f"""
✏️ **EDIT PHOTO POST**

🖼️ **Current caption:**
{data.get('caption', 'No caption')}

🎯 **Choose what to edit:**
"""
                bot.edit_message_text(edit_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')
    
    elif call.data == 'delete_content':
        if user_id in user_data:
            del user_data[user_id]
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_menu"))
        bot.edit_message_text("🗑️ **Content Deleted**\n\n✅ Your content has been removed.\n\nUse /start to create new content.", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')
        
    elif call.data == 'preview_content':
        data = user_data.get(user_id, {})
        if 'message_text' in data:
            preview_text = f"""
👁️ **FULL PREVIEW**

{data['message_text']}

——————————
📊 This is how your post will appear
"""
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔙 Back to Actions", callback_data="back_to_preview"))
            bot.edit_message_text(preview_text, call.message.chat.id, call.message.message_id, reply_markup=markup, entities=data.get('message_entities'))
        else:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔙 Back to Actions", callback_data="back_to_preview"))
            bot.edit_message_text("👁️ **Photo preview sent above**\n\n📷 Check the photo and caption", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')
            bot.send_photo(call.message.chat.id, data['photo_file_id'], caption=data['caption'], caption_entities=data.get('caption_entities'))
    
    elif call.data == 'proceed_to_channels':
        show_channels_inline(call)
    
    elif call.data == 'edit_caption':
        data = user_data.get(user_id, {})
        current_caption = data.get('caption', '')
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("💾 Save Caption", callback_data="save_caption"),
            types.InlineKeyboardButton("🔙 Back", callback_data="edit_content")
        )
        
        edit_text = f"""
✏️ **EDIT CAPTION**

💬 **Current caption:**
{current_caption}

✏️ **Send your new caption below:**
"""
        
        user_states[user_id] = 'edit_caption_text'
        bot.edit_message_text(edit_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')
    
    elif call.data == 'new_photo':
        user_states[user_id] = 'post_photo'
        bot.edit_message_text("🖼️ **UPLOAD NEW PHOTO**\n\n📷 Send your new photo with caption:", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
    
    elif call.data == 'save_caption':
        # This will be handled when user sends new caption text
        pass
    
    elif call.data == 'add_url_button':
        user_states[user_id] = 'add_url_button'
        bot.edit_message_text("🔗 **ADD URL BUTTON**\n\n🔗 **Just send the URL:**\n\n✨ **Example:**\n`https://manhwa.com`\n\n📝 Button text will be 'Read' by default", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
    
    elif call.data == 'toggle_notification':
        data = user_data.get(user_id, {})
        current_status = "🔕 ON" if not data.get('disable_notification', False) else "🔔 OFF"
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🔕 Turn ON", callback_data="notification_on"),
            types.InlineKeyboardButton("🔔 Turn OFF", callback_data="notification_off")
        )
        markup.add(types.InlineKeyboardButton("🔙 Back to Preview", callback_data="back_to_preview"))
        
        bot.edit_message_text(f"🔔 **NOTIFICATION SETTINGS**\n\n⚙️ **Current Status:** {current_status}\n\n🎯 **Choose notification setting:**", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')
    
    elif call.data == 'notification_on':
        if user_id in user_data:
            user_data[user_id]['disable_notification'] = False
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back to Preview", callback_data="back_to_preview"))
        bot.edit_message_text("🔕 **NOTIFICATIONS ENABLED**\n\n✅ Users will receive notifications when this post is published.\n\n✨ Setting saved!", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')
    
    elif call.data == 'notification_off':
        if user_id in user_data:
            user_data[user_id]['disable_notification'] = True
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back to Preview", callback_data="back_to_preview"))
        bot.edit_message_text("🔔 **NOTIFICATIONS DISABLED**\n\n🔇 Users will NOT receive notifications when this post is published.\n\n✨ Setting saved!", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')
    
    elif call.data == 'view_channels':
        show_channel_status(call)
    
    elif call.data == 'add_channel':
        bot.edit_message_text("➕ **ADD CHANNEL**\n\n🚀 **Coming Soon!**\n\nThis feature will allow you to add new channels to your bot.", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back to Channels", callback_data="back_to_channels"))
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == 'remove_channel':
        bot.edit_message_text("➖ **REMOVE CHANNEL**\n\n🚀 **Coming Soon!**\n\nThis feature will allow you to remove channels from your bot.", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back to Channels", callback_data="back_to_channels"))
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == 'back_to_channels':
        # Recreate channel management menu
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("📊 View Channels", callback_data="view_channels"),
            types.InlineKeyboardButton("➕ Add Channel", callback_data="add_channel")
        )
        markup.add(
            types.InlineKeyboardButton("➖ Remove Channel", callback_data="remove_channel"),
            types.InlineKeyboardButton("🔄 Refresh Status", callback_data="channel_status")
        )
        markup.add(
            types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_menu"),
            types.InlineKeyboardButton("❌ Cancel", callback_data="global_cancel")
        )
        
        channel_text = """
📢 **CHANNEL MANAGEMENT**

📊 **Current Channels:**
"""
        
        for name, channel in CHANNELS.items():
            channel_text += f"• **{name}**: {channel}\n"
        
        channel_text += "\n🎯 **Choose an action:**"
        
        bot.edit_message_text(channel_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')
    
    elif call.data == 'cancel_all':
        if user_id in user_data:
            del user_data[user_id]
        if user_id in user_states:
            del user_states[user_id]
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_menu"))
        bot.edit_message_text("❌ **ALL CANCELLED**\n\n✅ All content and settings have been cleared.\n\nYou can start fresh from the main menu.", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')
    
    elif call.data == 'back_to_preview':
        data = user_data.get(user_id, {})
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✏️ Edit", callback_data="edit_content"),
            types.InlineKeyboardButton("🗑️ Delete", callback_data="delete_content")
        )
        markup.add(
            types.InlineKeyboardButton("👁️ Preview", callback_data="preview_content"),
            types.InlineKeyboardButton("🚀 Send", callback_data="proceed_to_channels")
        )
        markup.add(
            types.InlineKeyboardButton("🔗 Add URL Button", callback_data="add_url_button"),
            types.InlineKeyboardButton("🔔 Notification", callback_data="toggle_notification")
        )
        markup.add(
            types.InlineKeyboardButton("❌ Cancel All", callback_data="cancel_all"),
            types.InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")
        )
        
        # Show enhanced preview with settings
        settings_info = ""
        if 'url_buttons' in data and data['url_buttons']:
            settings_info += f"\n🔗 **URL Buttons:** {len(data['url_buttons'])} added"
        
        notification_status = "🔕 ON" if not data.get('disable_notification', False) else "🔔 OFF"
        settings_info += f"\n🔔 **Notifications:** {notification_status}"
        
        if 'message_text' in data:
            preview_text = f"""
📝 **CONTENT PREVIEW**

✨ **Your message:**
{data.get('message_text', '')[:200]}{'...' if len(data.get('message_text', '')) > 200 else ''}{settings_info}

🎯 **Choose an action:**
"""
        else:
            caption_preview = data.get('caption', 'No caption')
            preview_text = f"""
🖼️ **PHOTO PREVIEW**

📷 **Photo uploaded successfully!**
💬 **Caption:** {caption_preview[:100]}{'...' if len(caption_preview) > 100 else ''}{settings_info}

🎯 **Choose an action:**
"""
        
        bot.edit_message_text(preview_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')

def show_channels_inline(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key in CHANNELS.keys():
        markup.add(types.InlineKeyboardButton(f"📢 {key}", callback_data=f"ch_{key}"))
    markup.add(types.InlineKeyboardButton("🚀 Post to Both Channels", callback_data="ch_all"))
    markup.add(
        types.InlineKeyboardButton("🔙 Back to Preview", callback_data="back_to_preview"),
        types.InlineKeyboardButton("❌ Cancel All", callback_data="global_cancel")
    )
    
    channel_text = """
🎯 **SELECT TARGET CHANNEL**

📢 Choose where to publish your content:

📚 **Manhwa_Digest** - Main content & reviews
🔄 **Ongoing_Manhwas** - Updates & new releases
🚀 **Both Channels** - Maximum reach!
"""
    
    bot.edit_message_text(channel_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data.startswith('ch_') or call.data == 'global_cancel')
@admin_required
def channel_callback(call):
    if call.data == 'global_cancel':
        user_id = call.from_user.id
        if user_id in user_data:
            del user_data[user_id]
        if user_id in user_states:
            del user_states[user_id]
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_menu"))
        bot.edit_message_text("❌ **ALL CANCELLED**\n\n✅ All content and settings have been cleared.\n\nYou can start fresh from the main menu.", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')
        return
    
    channel_key = call.data.replace('ch_', '')
    if channel_key == 'all':
        channels = list(CHANNELS.values())
    else:
        channels = [CHANNELS[channel_key]]
    
    post_to_channels(call, channels)

def post_to_channels(call, channels):
    import time
    user_id = call.from_user.id
    data = user_data.get(user_id, {})
    results = []
    
    try:
        # Show posting in progress message
        bot.edit_message_text("🚀 **POSTING IN PROGRESS...**\n\n⏳ Please wait while we publish your content...", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        
        for channel in channels:
            try:
                # Create URL buttons if any
                reply_markup = None
                if 'url_buttons' in data and data['url_buttons']:
                    markup = types.InlineKeyboardMarkup()
                    for button in data['url_buttons']:
                        markup.add(types.InlineKeyboardButton(button['text'], url=button['url']))
                    reply_markup = markup
                
                # Get notification setting
                disable_notification = data.get('disable_notification', False)
                
                if 'message_text' in data:
                    bot.send_message(
                        channel, 
                        data['message_text'], 
                        entities=data['message_entities'],
                        reply_markup=reply_markup,
                        disable_notification=disable_notification
                    )
                elif 'photo_file_id' in data:
                    bot.send_photo(
                        channel, 
                        data['photo_file_id'], 
                        caption=data['caption'], 
                        caption_entities=data.get('caption_entities'),
                        reply_markup=reply_markup,
                        disable_notification=disable_notification
                    )
                results.append(f"✅ {channel}")
            except Exception as e:
                results.append(f"❌ {channel}: {str(e)[:50]}")
        
        # Wait 2 seconds before showing results
        time.sleep(2)
        
    except Exception as e:
        results.append("❌ Critical error occurred")
    
    finally:
        # Always show results
        try:
            result_text = f"""
🎉 **POSTING COMPLETE!**

📊 **Results Summary:**

{chr(10).join(results)}

✨ Process finished!
🔙 Use /start to post more content
"""
            
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("📝 New Post", callback_data="create_post"),
                types.InlineKeyboardButton("📊 Status", callback_data="channel_status")
            )
            markup.add(types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_menu"))
            
            bot.edit_message_text(result_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')
            
        except Exception:
            # Fallback: simple message
            bot.edit_message_text("Posting completed! Check your channels.", call.message.chat.id, call.message.message_id)
        
        # Clean up user data
        if user_id in user_data:
            del user_data[user_id]

def show_channel_management_inline(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 View Channels", callback_data="view_channels"),
        types.InlineKeyboardButton("➕ Add Channel", callback_data="add_channel")
    )
    markup.add(
        types.InlineKeyboardButton("➖ Remove Channel", callback_data="remove_channel"),
        types.InlineKeyboardButton("🔄 Refresh Status", callback_data="channel_status")
    )
    markup.add(
        types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_menu"),
        types.InlineKeyboardButton("❌ Cancel", callback_data="global_cancel")
    )
    
    channel_text = """
📢 **CHANNEL MANAGEMENT**

📊 **Current Channels:**
"""
    
    for name, channel in CHANNELS.items():
        channel_text += f"• **{name}**: {channel}\n"
    
    channel_text += "\n🎯 **Choose an action:**"
    
    bot.edit_message_text(channel_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')

# Flask web server for Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Manhwa Bot is running! 🤖"

@app.route('/health')
def health():
    return "OK"

def keep_alive():
    """Keep the service alive by making periodic requests"""
    while True:
        try:
            time.sleep(300)  # Wait 5 minutes
            # Ping our own service to keep it alive
            requests.get('http://localhost:' + str(os.environ.get('PORT', 5000)) + '/health', timeout=10)
            print("Keep-alive ping sent")
        except Exception as e:
            print(f"Keep-alive error: {e}")

def run_bot():
    print("Manhwa Bot starting...")
    while True:
        try:
            bot.infinity_polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Bot error: {e}")
            print("Restarting bot in 15 seconds...")
            time.sleep(15)

if __name__ == "__main__":
    # Start keep-alive in background
    keep_alive_thread = threading.Thread(target=keep_alive)
    keep_alive_thread.daemon = True
    keep_alive_thread.start()
    
    # Start bot in a separate thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Start Flask web server
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)