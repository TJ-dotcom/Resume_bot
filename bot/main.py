from telegram.ext import Application
from .handlers import setup_handlers

def main():
    # Replace 'YOUR_API_TOKEN' with your actual Telegram bot API token
    application = Application.builder().token('8163454634:AAGwmRaAyj02ef6bxNfPnEInROivAPNeR7M').build()

    # Set up the handlers
    setup_handlers(application)

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()