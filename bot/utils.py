import requests
import logging
import time
import json
import os
from typing import Dict, Any, List
from yake import KeywordExtractor

# Configure logging
logging.basicConfig(
    filename=os.path.join(os.path.dirname(__file__), 'bot.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

QWEN_MODEL = "qwen2.5-7b-instruct-1m"
# Set the QWEN model endpoint
QWEN_API_URL = "http://127.0.0.1:1234/v1/chat/completions"
qwen_API_KEY = os.getenv("qwen_API_KEY", "")

def log_error(func):
    """Decorator to log errors in functions."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            raise
    return wrapper

@log_error
def generate_qwen_response(prompt: str) -> str:
    """
    Generate text using Qwen LLM.
    
    Args:
        prompt (str): The prompt to send to Qwen
        
    Returns:
        str: Generated response text
    """
    system_prompt = "You are an AI assistant specialized in resume enhancement and job applications."
    
    try:
        logger.info(f"Sending prompt to Qwen API: {prompt}")
        response = call_qwen_api(system_prompt, prompt)
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        logger.info(f"Received response from Qwen API: {content}")
        return content
    
    except Exception as e:
        logger.error(f"Error generating text with Qwen: {e}")
        return ""

@log_error
def extract_keywords_with_qwen(job_description: str) -> Dict:
    """Extract keywords from job description using Qwen API."""
    system_prompt = """
    You are a job analysis expert. Extract ALL TOP 10-12 keywords for skills, requirements, and qualifications
    from the provided job description using these guidelines:

    Technical Skills (8-12 keywords):
    - Software/tools (ERP, BI tools, databases)
    - Methodologies (Agile, DevOps)
    - Technical processes (Data modeling, ETL)
    - Industry-specific skills (FP&A, HIPAA compliance)

    Cloud Technologies (5-8 keywords):
    - Platforms (AWS, Azure, GCP)
    - Services (EC2, S3, Lambda)
    - Related tech (Kubernetes, Docker)

    Programming Knowledge (5-7 keywords):
    - Languages (Python, Java)
    - Frameworks (React, Django)
    - Paradigms (OOP, Functional)

    Soft Skills (5-7 keywords):
    - Team collaboration
    - Client communication
    - Strategic planning

    Extraction Rules:
    1. Identify both explicit and contextually implied keywords
    2. Include synonyms and related terms (e.g., "CI/CD" → "Jenkins")
    3. Capture multi-word phrases ("data pipeline optimization")
    4. Prioritize frequency and position (first 1/3 of JD)
    """
    user_message = job_description
    return call_qwen_api(system_prompt, user_message)

@log_error
def infuse_keywords(sections: Dict, keywords: Dict[str, List[str]]) -> Dict:
    """
    Infuse keywords into resume sections.
    Ensures relevant keywords are included without duplicates.
    
    Args:
        sections (dict): Resume sections
        keywords (dict): Extracted keywords from job description
        
    Returns:
        dict: Updated resume sections with infused keywords
    """
    # Add relevant keywords to skills section
    if "skills" not in sections:
        sections["skills"] = []

    existing_skills = set(s.lower() for s in sections["skills"])
    
    # Create a list of all unique keywords from all categories
    all_keywords = []
    for category, kw_list in keywords.items():
        for skill in kw_list:
            # Only add if not already in all_keywords (case-insensitive check)
            if not any(existing.lower() == skill.lower() for existing in all_keywords):
                all_keywords.append(skill)
        
    # Add unique keywords to skills section
    for skill in all_keywords:
        if skill.lower() not in existing_skills and not any(
            skill.lower() in existing.lower() or existing.lower() in skill.lower()
            for existing in sections["skills"]
        ):
            sections["skills"].append(skill)
            existing_skills.add(skill.lower())
    
    logger.info(f"Updated skills section with unique keywords. Total skills: {len(sections.get('skills', []))}")
    return sections

@log_error
def rephrase_and_tailor_resume(sections: Dict, keywords: Dict[str, List[str]], job_description: str) -> Dict:
    # Extract keywords using hybrid extraction
    extracted_keywords = hybrid_extraction(job_description)
    
    # Validate and filter keywords
    validated_keywords = validate_keywords(extracted_keywords, job_description)
    
    # Add keywords to skills section if not already present
    sections = infuse_keywords(sections, validated_keywords)
    
    return sections

@log_error
def extract_job_title(job_description: str) -> str:
    """Extract job title from job description."""
    # Simple heuristic - often the job title is in the first few lines
    first_lines = job_description.split("\n")[:3]
    for line in first_lines:
        if len(line.strip()) > 0 and len(line.strip().split()) <= 5:
            return line.strip()
    
    # Fallback - ask Qwen to extract it
    prompt = f"Extract only the job title from this job description:\n\n{job_description}"
    system_prompt = "You are a job analysis expert. Extract only the job title from the description."
    
    try:
        response = call_qwen_api(system_prompt, prompt)
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        return content.strip()
    except Exception:
        # Final fallback
        return "the position"

@log_error
def call_qwen_api(system_prompt: str, user_message: str) -> Dict:
    """
    Make an API call to the Qwen server.
    
    Args:
        system_prompt (str): The system prompt
        user_message (str): The user message
        
    Returns:
        dict: API response
    """
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "model": QWEN_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.2,
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(QWEN_API_URL, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to Qwen API: {e}")
        raise

@log_error
def extract_json_from_text(text: str) -> Dict:
    """
    Extract JSON from a text that might contain other content.
    
    Args:
        text (str): Text potentially containing JSON
        
    Returns:
        dict: Extracted JSON object
    """
    # Try to find JSON within markdown code blocks first
    if "```json" in text:
        try:
            start_idx = text.find("```json") + 7
            end_idx = text.find("```", start_idx)
            json_text = text[start_idx:end_idx].strip()
            return json.loads(json_text)
        except (ValueError, json.JSONDecodeError):
            pass
    
    # Try extracting any code block
    if "```" in text:
        try:
            start_idx = text.find("```") + 3
            # Skip the language identifier if present
            if text[start_idx:].strip().split("\n")[0].isalpha():
                start_idx = text.find("\n", start_idx) + 1
            end_idx = text.find("```", start_idx)
            json_text = text[start_idx:end_idx].strip()
            return json.loads(json_text)
        except (ValueError, json.JSONDecodeError):
            pass
    
    # Try parsing the entire text as JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Last resort, try to find anything that looks like JSON
        try:
            start_idx = text.find("{")
            end_idx = text.rfind("}") + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_text = text[start_idx:end_idx]
                return json.loads(json_text)
        except (ValueError, json.JSONDecodeError):
            pass
    
    # If all else fails, return an empty dict
    logger.warning("Could not extract JSON from qwen response")
    return {}

@log_error
def extract_text_from_file(file_path):
    """Extract text content from various file types."""
    file_extension = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_extension == '.pdf':
            # Extract text from PDF using PyPDF2
            import PyPDF2
            text = ""
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text
            
        elif file_extension == '.docx':
            # Extract text from DOCX using python-docx
            import docx
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
            
        elif file_extension == '.txt':
            # Read text file directly
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
                
        else:
            # Unsupported file type
            raise ValueError(f"Unsupported file type: {file_extension}")
            
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {e}")
        raise

def hybrid_extraction(jd_text: str) -> Dict:
    """Combine LLM and statistical extraction."""
    # LLM-based extraction
    llm_keywords = extract_keywords_with_qwen(jd_text)
    
    # YAKE fallback
    yake_extractor = KeywordExtractor(top=20)
    yake_keywords = yake_extractor.extract_keywords(jd_text)
    
    # Merge results
    for category in ["technical_skills", "cloud_technologies"]:
        llm_keywords[category] += [kw[0] for kw in yake_keywords 
                                   if relevant_to_category(kw[0], category)]
    
    return deduplicate_keywords(llm_keywords)

def relevant_to_category(keyword: str, category: str) -> bool:
    """Check if a keyword is relevant to a category."""
    # Implement your logic to determine relevance
    return True

def deduplicate_keywords(keywords: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Remove duplicate keywords."""
    for category in keywords:
        keywords[category] = list(set(keywords[category]))
    return keywords

def validate_keywords(keywords: Dict[str, List[str]], job_description: str) -> Dict[str, List[str]]:
    """Validate and filter keywords based on job description."""
    job_description_lower = job_description.lower()
    for category in keywords:
        keywords[category] = [kw for kw in keywords[category] 
                              if kw.lower() in job_description_lower 
                              or is_contextually_implied(kw, job_description)]
    return keywords

def is_contextually_implied(keyword: str, job_description: str) -> bool:
    """Check if a keyword is contextually implied in the job description."""
    # Implement your logic to determine contextual implication
    return True
