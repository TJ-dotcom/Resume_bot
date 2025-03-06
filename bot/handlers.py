from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler, ApplicationBuilder
import logging
import os
import json
import time
from bot.resume_parser import ResumeParser
from bot.deepseek_processor import QWENProcessor
from bot.utils import extract_keywords_with_huggingface
from bot.resume_enhancer import enhance_resume, save_json_file
from bot.rephrasing import enhance_resume_content

# Get logger for this module
logger = logging.getLogger(__name__)

# Create instances of ResumeParser and QWENProcessor
resume_parser = ResumeParser()
qwen_processor = QWENProcessor()

# States for the conversation
JOB_DESCRIPTION, RESUME = range(2)

# Global variable initializations
job_description = ""
resume_path = ""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a message when the command /start is issued."""
    # Reset global variables to ensure a fresh start
    global job_description, resume_path
    job_description = ""
    resume_path = ""
    
    logger.info("Command /start issued - resetting conversation")
    await update.message.reply_text('Hello! Share the job title and its description.')
    return JOB_DESCRIPTION

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    logger.info("Command /help issued")
    await update.message.reply_text(
        'Use /start to start the conversation.\n'
        'Send a job description to tailor your resume.\n'
        'Then upload your PDF resume to get a tailored version.'
    )

async def receive_job_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global job_description
    job_description = update.message.text
    logger.info(f"Received job description: {job_description}")
    await update.message.reply_text('Analyzing job description...')
    
    # Extract keywords using QWEN
    extracted_keywords = extract_keywords_with_huggingface(job_description)
    
    logger.info(f"Extracted Keywords: {extracted_keywords}")
    
    # Format keywords for display
    keywords_display = ", ".join(extracted_keywords)
    
    await update.message.reply_text(f"Extracted Keywords:\n{keywords_display}")
    await update.message.reply_text('Send your current resume in PDF format.')
    return RESUME

async def receive_files(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global resume_path
    chat_id = update.effective_chat.id
    document = update.message.document

    if document and document.file_name.lower().endswith('.pdf'):
        file_name = document.file_name
        file_path = os.path.join("data/resumes", file_name)
        resume_path = file_path

        # Ensure the resumes directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Download the file
        try:
            file = await context.bot.get_file(document.file_id)
            await file.download_to_drive(file_path)
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            await update.message.reply_text('Error downloading file. Please try again.')
            return RESUME

        logger.info(f"Received resume: {file_name}")
        await update.message.reply_text(f"Received {file_name}")

        # Process the files
        try:
            await process_files(job_description, resume_path, update, context)
        except Exception as e:
            logger.error(f"Error processing files: {e}")
            await update.message.reply_text("Sorry, we're facing an error. Please try restarting.")
            return ConversationHandler.END
        return ConversationHandler.END
    else:
        logger.warning("Unsupported file type received")
        await update.message.reply_text('Unsupported file type. Please send a .pdf resume.')
        return RESUME

async def process_files(job_description, resume_path, update, context):
    try:
        # Extract text from the resume
        resume_text = resume_parser.parse_resume(resume_path)
        
        if not resume_text:
            await update.message.reply_text("Failed to extract text from the resume. Please try again.")
            return ConversationHandler.END
        
        # Convert the extracted text to JSON using QWENProcessor
        qwen_processor = QWENProcessor()
        json_data = qwen_processor.convert_to_json(resume_text)
        
        if not json_data:
            await update.message.reply_text("Failed to convert resume text to JSON. Please try again.")
            return ConversationHandler.END
        
        # Enhance the resume content by rephrasing work experience and project descriptions
        extracted_keywords = extract_keywords_with_huggingface(job_description)
        enhanced_json_data = enhance_resume_content(json_data, extracted_keywords)
        
        # Save the enhanced JSON data to a file
        timestamp = int(time.time())
        output_dir = os.path.join("data/outputs")
        os.makedirs(output_dir, exist_ok=True)
        output_filename = os.path.join(output_dir, f"resume_{timestamp}.json")
        
        with open(output_filename, 'w', encoding='utf-8') as json_file:
            json.dump(enhanced_json_data, json_file, ensure_ascii=False, indent=4)
        
        logger.info(f"Enhanced resume JSON generated at {output_filename}")
        
        # Send the enhanced JSON file back to the user
        with open(output_filename, 'rb') as json_file:
            await context.bot.send_document(
                chat_id=update.effective_chat.id, 
                document=json_file,
                filename=os.path.basename(output_filename)
            )
        await update.message.reply_text('Your resume has been processed and enhanced.')
    
    except Exception as e:
        logger.error(f"Error in process_files: {e}", exc_info=True)
        await update.message.reply_text(f"An error occurred while processing your resume. Please try again.")
        raise

def setup_handlers(application):
    """Set up the command and message handlers for the bot."""
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            JOB_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_job_description)],
            RESUME: [MessageHandler(filters.Document.PDF, receive_files)]
        },
        fallbacks=[
            CommandHandler("start", start),  # Added /start as fallback to restart at any time
            CommandHandler("help", help_command)
        ]
    )
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a message to the user."""
    logger.error(f"Exception while handling an update: {context.error}")
    await update.message.reply_text('An unexpected error occurred. Please try again.')

if __name__ == "__main__":
    application = ApplicationBuilder().token("YOUR_BOT_TOKEN").build()
    setup_handlers(application)
    application.add_error_handler(error_handler)
    application.run_polling()