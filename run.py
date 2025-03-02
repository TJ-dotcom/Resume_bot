#!/usr/bin/env python
"""
Run the resume bot directly (avoiding module import issues)
"""
import os
import sys
import logging

# Change to the directory of this script
os.chdir(os.path.dirname(os.path.abspath(__file__)))

try:
    # Import and run from the direct path
    from bot.main import main
    main()
except ImportError as e:
    logging.error(f"Import error: {e}")
    print(f"Error importing modules: {e}")
    print("Make sure all dependencies are installed:")
    print("pip install python-telegram-bot requests PyPDF2 python-docx")
except Exception as e:
    logging.exception("Error running the bot")
    print(f"Error running the bot: {e}")
