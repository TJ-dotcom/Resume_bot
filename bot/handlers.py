from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler, ApplicationBuilder
import logging
import os
import sys
import time
import json

# Add current directory to path for local imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Local imports
from pdf_generator import generate_resume_pdf, generate_simple_pdf
from resume_parser import parse_resume, parse_extracted_text
from utils import extract_keywords_with_deepseek, generate_deepseek_response, infuse_keywords, rephrase_and_tailor_resume
from json_resume_converter import convert_to_json_resume, convert_from_json_resume

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
    
    try:
        # Send status messages to keep the user informed
        await update.message.reply_text("Parsing your resume...")
        
        parsed_data = parse_resume(resume_path)
        
        # Store original content for verification
        original_resume = {}
        
        # Check if parsed_data is a dictionary with a 'text' key
        if isinstance(parsed_data, dict) and "text" in parsed_data:
            resume_text = parsed_data["text"]
        else:
            # If parsed_data is already a string or has unexpected format
            resume_text = str(parsed_data)
            
        logger.info(f"Resume text extracted successfully. Length: {len(resume_text)}")
        
        # Parse the extracted text into sections
        sections = parse_extracted_text(resume_text)
        
        # Store original sections for comparison
        for key in sections:
            if isinstance(sections[key], list):
                original_resume[key] = sections[key].copy()
        
        # Progress update
        await update.message.reply_text("Tailoring your resume to match the job description...")
        
        # Infuse keywords into the resume sections (focusing on skills section)
        tailored_sections = infuse_keywords(sections, extracted_keywords)
        
        # Rephrase and tailor the resume content using DeepSeek (focusing on experience and projects)
        tailored_sections = rephrase_and_tailor_resume(tailored_sections, extracted_keywords, job_description)
        
        # Verify that content was actually modified
        modification_verified = verify_content_modification(original_resume, tailored_sections)
        
        if not modification_verified:
            # If content wasn't modified enough, force another round of tailoring
            logger.warning("Content not sufficiently modified. Attempting deeper tailoring.")
            tailored_sections = force_deeper_tailoring(tailored_sections, extracted_keywords, job_description)
        
        # Progress update
        await update.message.reply_text("Generating your tailored resume as PDF...")
        
        # Generate unique filename based on timestamp in the resumes folder
        timestamp = int(time.time())
        output_dir = os.path.join("resumes", "outputs")
        os.makedirs(output_dir, exist_ok=True)
        output_filename = os.path.join(output_dir, f"tailored_resume_{timestamp}.pdf")
        
        # Try to generate PDF
        tailored_resume_path = generate_resume_pdf(
            tailored_sections, 
            output_filename,
            force_pdf=True  # Always try to force PDF output
        )
        
        logger.info(f"Resume generated at {tailored_resume_path}")
        
        # Send the tailored resume back to the user
        if os.path.exists(tailored_resume_path):
            with open(tailored_resume_path, 'rb') as resume_file:
                await context.bot.send_document(
                    chat_id=update.effective_chat.id, 
                    document=resume_file,
                    filename=os.path.basename(tailored_resume_path)
                )
            await update.message.reply_text('Your tailored resume has been processed as PDF and sent back to you.')
        else:
            raise FileNotFoundError(f"Generated file not found: {tailored_resume_path}")
    
    except Exception as e:
        logger.error(f"Error in process_files: {e}", exc_info=True)
        await update.message.reply_text(f"An error occurred while processing your resume. Please try again.")
        raise

def verify_content_modification(original, tailored):
    """
    Verify that the tailored content is sufficiently different from the original.
    
    Args:
        original (dict): Original resume sections
        tailored (dict): Tailored resume sections
        
    Returns:
        bool: True if content was modified beyond a threshold, False otherwise
    """
    if not original or not tailored:
        return True  # Can't verify, assume it's ok
        
    # Count modifications
    modifications = 0
    total_items = 0
    
    for section in ['experience', 'projects', 'skills']:
        if section in original and section in tailored:
            orig_items = original[section]
            tail_items = tailored[section]
            
            # If lengths differ, content was definitely modified
            if len(orig_items) != len(tail_items):
                return True
                
            for i in range(min(len(orig_items), len(tail_items))):
                total_items += 1
                if orig_items[i] != tail_items[i]:
                    modifications += 1
    
    # If at least 40% of content was modified, consider it sufficient
    return total_items == 0 or (modifications / total_items) >= 0.4

def force_deeper_tailoring(sections, keywords, job_description):
    """
    Force deeper tailoring when initial tailoring wasn't sufficient.
    
    Args:
        sections (dict): Resume sections
        keywords (dict): Extracted keywords
        job_description (str): Job description
        
    Returns:
        dict: More thoroughly tailored resume sections
    """
    logger.info("Forcing deeper tailoring of resume content")
    
    # Create a stronger prompt that emphasizes the need for significant changes
    stronger_prompt = (
        f"You MUST significantly modify and enhance the following resume sections to "
        f"match the job description. The previous modifications were insufficient. "
        f"Make substantial changes while keeping the core information intact.\n\n"
        f"Job Description:\n{job_description}\n\n"
    )
    
    # Specially handle each section
    for section in ['experience', 'projects', 'skills']:
        if section in sections and isinstance(sections[section], list):
            for i, item in enumerate(sections[section]):
                if section == 'skills':
                    continue  # Skills are best handled by the infuse_keywords function
                
                prompt = stronger_prompt + f"Content to significantly enhance:\n{item}\n\nKeywords to incorporate: "
                prompt += ", ".join([kw for category in keywords.values() for kw in category])
                
                # Get stronger tailoring
                enhanced_content = generate_deepseek_response(prompt)
                
                # Only use the response if it's not too short
                if enhanced_content and len(enhanced_content) > 20:
                    # For experience/projects, preserve company/project name format
                    if ':' in item:
                        prefix = item.split(':', 1)[0]
                        sections[section][i] = f"{prefix}: {enhanced_content}"
                    else:
                        sections[section][i] = enhanced_content
    
    return sections

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