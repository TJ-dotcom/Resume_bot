#!/bin/bash
# Define the progress log file
PROGRESS_LOG="progress_log.md"
# Get the latest commit message
COMMIT_MESSAGE=$(git log -1 --pretty=format:"%s")
# Get the current date and time
CURRENT_DATE=$(date +'%B %d, %Y %H:%M:%S')
# Append the progress to the log file
{
  echo "## $CURRENT_DATE"
  echo "- $COMMIT_MESSAGE"
  echo ""
} >> $PROGRESS_LOG