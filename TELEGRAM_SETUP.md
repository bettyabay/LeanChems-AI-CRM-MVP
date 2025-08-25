# Telegram Notification Setup Guide

This guide will help you set up daily morning notifications for your LeanChems CRM system via Telegram.

## Prerequisites

1. A Telegram account
2. Python environment with the required dependencies installed

## Step 1: Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Start a conversation with BotFather
3. Send the command `/newbot`
4. Follow the instructions to create your bot:
   - Choose a name for your bot (e.g., "LeanChems CRM Bot")
   - Choose a username for your bot (must end with 'bot', e.g., "leanchems_crm_bot")
5. BotFather will give you a **Bot Token** - save this securely

## Step 2: Get Your Chat ID

1. Start a conversation with your newly created bot
2. Send any message to the bot (e.g., "Hello")
3. Open a web browser and go to: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Replace `<YOUR_BOT_TOKEN>` with the actual token from Step 1
4. Look for the `"chat":{"id":123456789}` in the response
5. The number (e.g., `123456789`) is your **Chat ID**

## Step 3: Configure Environment Variables

Add the following variables to your `.env` file:

```env
# Telegram Notification Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
NOTIFICATION_ENABLED=true
```

## Step 4: Install Dependencies

Make sure you have the required packages installed:

```bash
pip install python-telegram-bot schedule
```

Or update your requirements.txt and run:

```bash
pip install -r requirements.txt
```

## Step 5: Test the Integration

1. Start your CRM application
2. Go to the "Analysis & Reporting" section
3. Scroll down to the "Telegram Notifications" section
4. Click "Send Test Notification" to verify everything is working

## Step 6: Daily Notifications

Once configured, the system will automatically send daily notifications at 8:00 AM containing:

- Summary of all active deals
- Customer count and deal status
- Action items for the day
- Quick tips and insights

## Troubleshooting

### Common Issues:

1. **"Telegram notifications not properly configured"**
   - Check that all environment variables are set correctly
   - Verify your bot token and chat ID

2. **"Failed to send test notification"**
   - Ensure your bot is active and you've sent it a message
   - Check your internet connection
   - Verify the bot token is correct

3. **Notifications not sending automatically**
   - Make sure `NOTIFICATION_ENABLED=true` in your .env file
   - Check that the application is running continuously
   - Verify the scheduler started successfully (check console logs)

### Manual Testing:

You can manually send a daily summary anytime by clicking "Send Daily Summary Now" in the Telegram Notifications section.

## Security Notes

- Keep your bot token secure and never share it publicly
- The bot will only send messages to the specified chat ID
- You can revoke and regenerate your bot token anytime via @BotFather

## Customization

You can modify the notification schedule by editing the `start_notification_scheduler()` function in the code:

```python
# Change from 8:00 AM to 9:00 AM
schedule.every().day.at("09:00").do(send_daily_notification)
```

The notification content can also be customized by modifying the `generate_daily_deal_summary()` function.

