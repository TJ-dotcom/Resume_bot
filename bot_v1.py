import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from bot.handlers import start, help_command, receive_job_description, receive_files
from bot.resume_parser import parse_resume
from bot.t5_model import generate_section_content
from bot.pdf_generator import save_as_pdf
import os

# Enable logging
logging.basicConfig(
    filename='bot.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Replace 'YOUR_TELEGRAM_BOT_TOKEN' with your actual bot token
TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'

# States for the conversation
JOB_DESCRIPTION, RESUME = range(2)

async def process_files(job_description, resume_path, update, context):
    try:
        await update.message.reply_text('Processing...')
        
        # Parse resume
        resume_data = parse_resume(resume_path)
        logger.info(f"Parsed resume data: {resume_data}")
        
        if "text" in resume_data:
            resume_data = parse_extracted_text(resume_data["text"])
        
        tailored_resume_data = {
            "name": resume_data.get('name', 'Unknown'),
            "skills": resume_data.get('skills', []) or ["No skills listed"],
            "experience": resume_data.get('experience', []) or [{"designation": "No experience listed", "company": "", "start_date": "", "end_date": "", "description": ""}],
            "education": resume_data.get('education', []) or [{"degree": "No education listed", "major": "", "institution": "", "year_of_passing": ""}],
            "projects": resume_data.get('projects', []) or [{"title": "No projects listed", "details": ""}],
            "certifications": resume_data.get('certifications', []) or ["No certifications listed"]
        }
        
        logger.info(f"Tailored resume data: {tailored_resume_data}")
        
        for section in ["summary", "skills", "experience", "education", "projects", "achievements", "certifications"]:
            if section in tailored_resume_data:
                tailored_resume_data[section] = generate_section_content(section, ensure_str_field(tailored_resume_data[section], section))
        
        tailored_resume_content = generate_resume_content(tailored_resume_data)
        
        tailored_resume_path = "tailored_resume.pdf"
        save_as_pdf(tailored_resume_content, tailored_resume_path)
        
        with open(tailored_resume_path, 'rb') as file:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=file)
        
        os.remove(resume_path)
        os.remove(tailored_resume_path)
    except Exception as e:
        logger.error(f"Error processing files: {e}")
        await update.message.reply_text('An error occurred while processing your resume.')

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            JOB_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_job_description)],
            RESUME: [MessageHandler(filters.Document.PDF, receive_files)]
        },
        fallbacks=[CommandHandler("help", help_command)]
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))

    application.run_polling()

if __name__ == '__main__':
    main()