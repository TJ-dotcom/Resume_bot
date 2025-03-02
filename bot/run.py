#!/usr/bin/env python
"""
Runner script for the resume bot.
This script runs the bot from outside the package to avoid import issues.
"""

import sys
import os
import logging
from resume_bot.bot.main import main

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception("Error running the bot: %s", e)
        sys.exit(1)
