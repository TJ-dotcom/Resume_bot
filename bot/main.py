from telegram.ext import ApplicationBuilder
import logging
import os
from .handlers import setup_handlers, error_handler

# Configure logging
logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Start the bot."""
    try:
        # Set your bot token directly
        token = "8163454634:AAGwmRaAyj02ef6bxNfPnEInROivAPNeR7M"
        
        # Create the application
        application = ApplicationBuilder().token(token).build()

        # Set up handlers
        setup_handlers(application)
        
        # Register error handler
        application.add_error_handler(error_handler)
        
        # Start the bot
        logger.info("Starting bot...")
        print("Bot is running...")
        application.run_polling()
    
    except Exception as e:
        logger.error(f"Error starting bot: {e}", exc_info=True)
        print(f"Error starting bot: {e}")

if __name__ == "__main__":
    main()