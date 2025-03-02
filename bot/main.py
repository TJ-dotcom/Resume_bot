import logging
import os
import sys

# Add current directory to path for local imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Now we can import local modules 
from handlers import setup_handlers, error_handler
from telegram.ext import ApplicationBuilder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Start the bot."""
    # Use your bot token here
    application = ApplicationBuilder().token("8163454634:AAGwmRaAyj02ef6bxNfPnEInROivAPNeR7M").build()
    
    # Set up handlers
    setup_handlers(application)
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the Bot
    application.run_polling()
    
    logging.info("Bot started.")

if __name__ == "__main__":
    main()