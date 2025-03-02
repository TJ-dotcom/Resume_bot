from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler, ApplicationBuilder
import logging
import os
import time
from .pdf_generator import generate_resume_pdf
from .resume_parser import parse_resume, parse_extracted_text
from .utils import (
    extract_keywords_with_deepseek,
    generate_deepseek_response,
    infuse_keywords,
    rephrase_and_tailor_resume
)

# Configure logging
logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    await update.message.reply_text('Use /start to start the conversation.\nSend a job description to tailor your resume.\nAsk "search entry level jobs with visa sponsorship" to find relevant jobs.')

async def receive_job_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global job_description
    job_description = update.message.text
    logger.info(f"Received job description: {job_description}")
    await update.message.reply_text('Analyzing job description...')
    
    # Extract keywords using DeepSeek
    extracted_keywords = extract_keywords_with_deepseek(job_description)
    
    logger.info(f"Extracted Keywords: {extracted_keywords}")
    
    # Format keywords for display
    keywords_display = []
    for category, keywords in extracted_keywords.items():
        if keywords:
            category_name = category.replace("_", " ").title()
            keywords_display.append(f"• {category_name}: {', '.join(keywords)}")
    
    formatted_keywords = "\n".join(keywords_display)
    await update.message.reply_text(f"Extracted Keywords:\n{formatted_keywords}")
    await update.message.reply_text('Send your current resume in PDF format.')
    return RESUME

async def receive_files(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global resume_path
    chat_id = update.effective_chat.id
    document = update.message.document

    if document and document.file_name.lower().endswith('.pdf'):
        file_name = document.file_name
        file_path = os.path.join("resumes", file_name)
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
    # Extract keywords from the job description
    extracted_keywords = extract_keywords_with_deepseek(job_description)
    
    # Parse the resume
    try:
        # Send status messages to keep the user informed
        await update.message.reply_text("Parsing your resume...")
        
        parsed_data = parse_resume(resume_path)
        
        # Check if parsed_data is a dictionary with a 'text' key
        if isinstance(parsed_data, dict) and "text" in parsed_data:
            resume_text = parsed_data["text"]
        else:
            # If parsed_data is already a string or has unexpected format
            resume_text = str(parsed_data)
            
        logger.info(f"Resume text extracted successfully. Length: {len(resume_text)}")
        
        # Parse the extracted text into sections
        sections = parse_extracted_text(resume_text)
        
        # Progress update
        await update.message.reply_text("Tailoring your resume to match the job description...")
        
        # Infuse keywords into the resume sections (focusing on skills section)
        tailored_sections = infuse_keywords(sections, extracted_keywords)
        
        # Rephrase and tailor the resume content using DeepSeek (focusing on experience and projects)
        tailored_sections = rephrase_and_tailor_resume(tailored_sections, extracted_keywords, job_description)
        
        # Progress update
        await update.message.reply_text("Generating your tailored resume document...")
        
        # Add error handling around the PDF generation
        try:
            # Generate the tailored resume
            tailored_resume_path = generate_resume_pdf(tailored_sections, "tailored_resume.pdf")
            
            logger.info(f"Tailored resume created at {tailored_resume_path}")
            
            # Send the tailored resume back to the user
            await context.bot.send_document(chat_id=update.effective_chat.id, document=open(tailored_resume_path, 'rb'))
            await update.message.reply_text('Your tailored resume has been processed and sent back to you.')
        except Exception as pdf_error:
            logger.error(f"Error generating PDF: {pdf_error}", exc_info=True)
            # Create a simple text file with the resume content
            text_output = "tailored_resume.txt"
            with open(text_output, "w", encoding="utf-8") as f:
                f.write("# TAILORED RESUME\n\n")
                f.write("## Skills\n")
                for skill in tailored_sections.get('skills', []):
                    f.write(f"- {skill}\n")
                f.write("\n## Experience\n")
                for exp in tailored_sections.get('experience', []):
                    f.write(f"- {exp}\n")
                f.write("\n## Projects\n")
                for proj in tailored_sections.get('projects', []):
                    f.write(f"- {proj}\n")
                
            await context.bot.send_document(chat_id=update.effective_chat.id, document=open(text_output, 'rb'))
            await update.message.reply_text('Your tailored resume has been processed as a text file due to PDF generation issues.')
    
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