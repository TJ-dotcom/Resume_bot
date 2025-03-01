from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler
import logging
import spacy
import os
import requests
from fpdf import FPDF
from .resume_parser import parse_resume, parse_extracted_text

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

# Load the spaCy model
nlp = spacy.load("en_core_web_sm")

# Set DeepSeek API key
deepseek_api_key = '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'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a message when the command /start is issued."""
    logger.info("Command /start issued")
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
    await update.message.reply_text('Loading...')
    
    # Extract keywords using spaCy
    extracted_keywords = extract_keywords(job_description)
    
    logger.info(f"Extracted Keywords: {extracted_keywords}")
    
    await update.message.reply_text(f'Extracted Keywords:\n{", ".join(extracted_keywords)}')
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
        file = await context.bot.get_file(document.file_id)
        await file.download_to_drive(file_path)

        logger.info(f"Received resume: {file_name}")
        await update.message.reply_text(f"Received {file_name}")

        # Process the files
        await process_files(job_description, resume_path, update, context)
        return ConversationHandler.END
    else:
        logger.warning("Unsupported file type received")
        await update.message.reply_text('Unsupported file type. Please send a .pdf resume.')
        return RESUME

def extract_keywords(job_description):
    doc = nlp(job_description)
    keywords = set()
    for token in doc:
        if token.pos_ in ["NOUN", "PROPN", "ADJ"]:  # Extract nouns, proper nouns, and adjectives
            keywords.add(token.text)
    return keywords

def infuse_keywords(sections, keywords):
    for keyword in keywords:
        if "skills" in sections and isinstance(sections["skills"], list):
            if keyword not in sections["skills"]:
                sections["skills"].append(keyword)
        if "experience" in sections and isinstance(sections["experience"], list):
            if keyword not in sections["experience"]:
                sections["experience"].append(f"Experience with {keyword}")
        if "projects" in sections and isinstance(sections["projects"], list):
            if keyword not in sections["projects"]:
                sections["projects"].append(f"Project involving {keyword}")

    return sections

def generate_tailored_resume(sections, original_resume_path):
    tailored_resume_path = original_resume_path.replace(".pdf", "_tailored.pdf")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for section, content in sections.items():
        pdf.cell(200, 10, txt=section.capitalize(), ln=True, align='L')
        for line in content:
            pdf.cell(200, 10, txt=line.encode('latin-1', 'replace').decode('latin-1'), ln=True, align='L')
        pdf.ln(10)

    pdf.output(tailored_resume_path)
    return tailored_resume_path

def generate_deepseek_response(prompt):
    headers = {
        'Authorization': f'Bearer {deepseek_api_key}',
        'Content-Type': 'application/json',
    }
    data = {
        'prompt': prompt,
        'max_tokens': 150,
        'temperature': 0.7,
    }
    response = requests.post('https://api.deepseek.com/v1/completions', headers=headers, json=data)
    response.raise_for_status()
    return response.json()['choices'][0]['text'].strip()

async def process_files(job_description, resume_path, update, context):
    # Extract keywords from the job description
    extracted_keywords = extract_keywords(job_description)
    
    # Parse the resume
    parsed_data = parse_resume(resume_path)
    sections = parse_extracted_text(parsed_data["text"])
    
    # Infuse keywords into the resume sections
    tailored_sections = infuse_keywords(sections, extracted_keywords)
    
    # Generate tailored content using DeepSeek
    for section in tailored_sections:
        prompt = f"Rewrite the following {section} section of a resume to better match the job description:\n\nJob Description:\n{job_description}\n\n{section.capitalize()} Section:\n{tailored_sections[section]}"
        tailored_sections[section] = generate_deepseek_response(prompt)
    
    # Generate the tailored resume
    tailored_resume_path = generate_tailored_resume(tailored_sections, resume_path)

    logger.info(f"Tailored resume created at {tailored_resume_path}")

    # Send the tailored resume back to the user
    await context.bot.send_document(chat_id=update.effective_chat.id, document=open(tailored_resume_path, 'rb'))
    await update.message.reply_text('Your tailored resume has been processed and sent back to you.')

def setup_handlers(application):
    """Set up the command and message handlers for the bot."""
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