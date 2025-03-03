#!/usr/bin/env python
"""
Runner script for the resume bot.
This script runs the bot from outside the package to avoid import issues.
"""

import sys
import os
import logging
from bot.main import main, setup_logging

if __name__ == "__main__":
    # Initialize logging
    logger = setup_logging()
    
    try:
        logger.info("Starting Resume Bot from run.py")
        main()
    except Exception as e:
        logger.exception("Error running the bot: %s", e)
        sys.exit(1)
