from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler
import logging
import spacy
import os
import json
import requests
from fpdf import FPDF, errors as fpdf_errors
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

# Set the DeepSeek model endpoint
deepseek_endpoint = 'http://127.0.0.1:1234/v1/completions'

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
    
    # Extract keywords using DeepSeek
    extracted_keywords = extract_keywords_with_deepseek(job_description)
    
    logger.info(f"Extracted Keywords: {extracted_keywords}")
    
    await update.message.reply_text(f'Extracted Keywords:\n{", ".join(extracted_keywords["technical_skills"] | extracted_keywords["soft_skills"] | extracted_keywords["programming_languages"] | extracted_keywords["technical_tools"] | extracted_keywords["data_tools"] | extracted_keywords["cloud_technologies"])}')
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
        await process_files(job_description, resume_path, update, context)
        return ConversationHandler.END
    else:
        logger.warning("Unsupported file type received")
        await update.message.reply_text('Unsupported file type. Please send a .pdf resume.')
        return RESUME

def generate_deepseek_response(prompt):
    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        'model': 'deepseek-coder-v2-lite-instruct',  # Specify the model
        'prompt': prompt,
        'max_tokens': 150,
        'temperature': 0.7,
    }
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(deepseek_endpoint, headers=headers, json=data)
            response.raise_for_status()
            response_json = response.json()
            logger.info(f"DeepSeek API response: {response_json}")
            if 'choices' in response_json:
                return response_json['choices'][0]['text'].strip()
            else:
                logger.error(f"Unexpected response format: {response_json}")
                return "Error: Unexpected response format from DeepSeek API"
        except requests.exceptions.RequestException as err:
            logger.error(f"Request error occurred: {err}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying... ({attempt + 1}/{max_retries})")
                time.sleep(2)  # Wait for 2 seconds before retrying
            else:
                return f"Error: {err}"

def extract_keywords_with_deepseek(job_description):
    prompt = (
        f"Extract the following categories of keywords from the job description:\n\n"
        f"Job Description:\n{job_description}\n\n"
        f"Categories:\n"
        f"1. Technical Skills\n"
        f"2. Soft Skills\n"
        f"3. Programming Languages\n"
        f"4. Technical Tools\n"
        f"5. Data Tools\n"
        f"6. Cloud Technologies\n\n"
        f"Provide the keywords in the following JSON format:\n"
        f"{{\n"
        f"  \"technical_skills\": [\"skill1\", \"skill2\", ...],\n"
        f"  \"soft_skills\": [\"skill1\", \"skill2\", ...],\n"
        f"  \"programming_languages\": [\"language1\", \"language2\", ...],\n"
        f"  \"technical_tools\": [\"tool1\", \"tool2\", ...],\n"
        f"  \"data_tools\": [\"tool1\", \"tool2\", ...],\n"
        f"  \"cloud_technologies\": [\"technology1\", \"technology2\", ...]\n"
        f"}}"
    )
    response = generate_deepseek_response(prompt)
    logger.info(f"DeepSeek keyword extraction response: {response}")
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON response: {e}")
        return {
            "technical_skills": [],
            "soft_skills": [],
            "programming_languages": [],
            "technical_tools": [],
            "data_tools": [],
            "cloud_technologies": []
        }

def infuse_keywords(sections, keywords):
    for keyword in keywords["technical_skills"]:
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
        pdf.set_font("Arial", 'B', size=14)
        pdf.cell(200, 10, txt=section.capitalize(), ln=True, align='L')
        pdf.set_font("Arial", size=12)
        for line in content:
            try:
                # Handle bullet points
                if line.startswith("- "):
                    pdf.cell(10, 10, txt="•", ln=False, align='L')
                    pdf.multi_cell(0, 10, txt=line[2:].encode('latin-1', 'replace').decode('latin-1'), align='L')
                else:
                    pdf.multi_cell(0, 10, txt=line.encode('latin-1', 'replace').decode('latin-1'), align='L')
            except fpdf_errors.FPDFException as e:
                logger.error(f"Error rendering text: {line}")
                logger.error(e)
                pdf.multi_cell(0, 10, txt="Error rendering text", align='L')
        pdf.ln(10)

    pdf.output(tailored_resume_path)
    return tailored_resume_path

import time

async def process_files(job_description, resume_path, update, context):
    # Extract keywords from the job description
    extracted_keywords = extract_keywords_with_deepseek(job_description)
    
    # Parse the resume
    parsed_data = parse_resume(resume_path)
    sections = parse_extracted_text(parsed_data["text"])
    
    # Infuse keywords into the resume sections
    tailored_sections = infuse_keywords(sections, extracted_keywords)
    
    # Generate tailored content using DeepSeek
    for section in tailored_sections:
        if section == "projects":
            for i, line in enumerate(tailored_sections[section]):
                prompt = (
                    f"Rewrite the following project description to better match the job description:\n\n"
                    f"Job Description:\n{job_description}\n\n"
                    f"Project Description:\n{line}\n\n"
                    f"Ensure the description includes the following keywords:\n"
                    f"Technical Skills: {', '.join(extracted_keywords['technical_skills'])}\n"
                    f"Soft Skills: {', '.join(extracted_keywords['soft_skills'])}\n"
                    f"Programming Languages: {', '.join(extracted_keywords['programming_languages'])}\n"
                    f"Technical Tools: {', '.join(extracted_keywords['technical_tools'])}\n"
                    f"Data Tools: {', '.join(extracted_keywords['data_tools'])}\n"
                    f"Cloud Technologies: {', '.join(extracted_keywords['cloud_technologies'])}."
                )
                tailored_sections[section][i] = generate_deepseek_response(prompt)
    
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