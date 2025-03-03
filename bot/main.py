import logging
import os
import sys
import argparse
from pathlib import Path

# Import our modules
from bot.resume_parser import ResumeParser
from bot.deepseek_processor import QWENProcessor  # Updated import

# Configure logging to both console and file
def setup_logging():
    """Configure logging for the application."""
    log_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(log_dir, 'bot.log')
    
    # Create a formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicate logs
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)
    
    # Add file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def setup_environment():
    """Set up the environment for the bot."""
    # Add current directory to path for local imports
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.append(current_dir)
    
    # Create necessary directories
    os.makedirs(os.path.join(current_dir, '..', 'data', 'resumes'), exist_ok=True)
    os.makedirs(os.path.join(current_dir, '..', 'data', 'outputs'), exist_ok=True)

def main():
    """Start the bot."""
    # Setup logging first
    logger = setup_logging()
    logger.info("Starting bot initialization...")
    
    # Setup environment
    setup_environment()
    
    # Now we can import local modules (after environment setup)
    from handlers import setup_handlers, error_handler
    from telegram.ext import ApplicationBuilder
    
    # Use environment variable for token or fallback to default
    token = "8163454634:AAGwmRaAyj02ef6bxNfPnEInROivAPNeR7M"
    
    # Initialize the application
    application = ApplicationBuilder().token(token).build()
    
    # Set up handlers
    setup_handlers(application)
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the Bot
    logger.info("Bot started and polling...")
    application.run_polling()
    
    logger.info("Bot stopped.")

if __name__ == "__main__":
    main()