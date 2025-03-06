import requests
import logging
import time
import json
import os
from typing import Dict, Any, List
from yake import KeywordExtractor
from transformers import pipeline, T5Tokenizer, T5ForConditionalGeneration
from keybert import KeyBERT
import re

# Configure logging
logging.basicConfig(
    filename=os.path.join(os.path.dirname(__file__), 'bot.log'),
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)

QWEN_MODEL = "qwen2.5-7b-instruct-1m"
# Set the QWEN model endpoint
QWEN_API_URL = "http://127.0.0.1:1234/v1/chat/completions"
qwen_API_KEY = os.getenv("qwen_API_KEY", "")

# Initialize Hugging Face models
try:
    tech_extractor = pipeline("text2text-generation", model="ilsilfverskiold/tech-keywords-extractor", max_length=150)
    classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
except Exception as e:
    logger.error(f"Error loading models: {e}")
    raise

try:
    t5_tokenizer = T5Tokenizer.from_pretrained("Voicelab/vlt5-base-keywords")
    t5_model = T5ForConditionalGeneration.from_pretrained("Voicelab/vlt5-base-keywords")
except Exception as e:
    logger.error(f"Error loading vlt5 model: {e}")
    raise

kw_model = KeyBERT()
yake_extractor = KeywordExtractor(top=20)

# Define categories for classification
CATEGORIES = ["technical skills", "soft skills", "programming", "tools", "management skills"]

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
def extract_keywords_with_huggingface(job_description: str) -> List[str]:
    """Extract keywords from job description using Hugging Face models."""
    try:
        # Technical skills extraction
        tech_output = tech_extractor(job_description)
        tech_keywords = extract_tech_keywords(tech_output[0]['generated_text'])
        
        # Contextual phrases extraction
        context_keywords = extract_contextual_phrases(job_description)
        
        # Merge results
        merged_keywords = merge_keywords(tech_keywords, context_keywords)
        
        # Use fallback mechanisms to extract additional keywords
        fallback_keywords = hybrid_fallback(job_description)
        
        # Combine all keywords
        combined_keywords = combine_keywords(merged_keywords, fallback_keywords)
        
        # Deduplicate keywords
        unique_keywords = deduplicate_keywords(combined_keywords)
        
        # Sort keywords alphabetically
        sorted_keywords = sorted(unique_keywords)
        
        return sorted_keywords
    except Exception as e:
        logger.error(f"Error in extract_keywords_with_huggingface, using fallback: {e}")
        return hybrid_fallback(job_description)

def extract_tech_keywords(output: str) -> List[str]:
    """Extract technical keywords from model output."""
    return list(set(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', output)))

def extract_contextual_phrases(jd_text: str) -> List[str]:
    """Extract contextual phrases using T5 model."""
    inputs = t5_tokenizer("Keywords: " + jd_text, return_tensors="pt", truncation=True)
    outputs = t5_model.generate(**inputs, no_repeat_ngram_size=3, num_beams=4)
    return t5_tokenizer.decode(outputs[0], skip_special_tokens=True).split(", ")

def hybrid_fallback(jd_text: str) -> List[str]:
    """Fallback keyword extraction using KeyBERT and YAKE."""
    keybert_keywords = [kw[0] for kw in kw_model.extract_keywords(jd_text)]
    yake_keywords = [kw[0] for kw in yake_extractor.extract_keywords(jd_text)]
    return keybert_keywords + yake_keywords

def combine_keywords(primary_keywords: List[str], fallback_keywords: List[str]) -> List[str]:
    """Combine primary and fallback keywords."""
    combined_keywords = primary_keywords + fallback_keywords
    return combined_keywords

def merge_keywords(tech_keywords: List[str], context_keywords: List[str]) -> List[str]:
    """Merge technical and contextual keywords."""
    return tech_keywords + context_keywords

def deduplicate_keywords(keywords: List[str]) -> List[str]:
    """Remove duplicate keywords."""
    seen = set()
    unique_keywords = []
    for keyword in keywords:
        lower_keyword = keyword.lower()
        if lower_keyword not in seen:
            unique_keywords.append(keyword)
            seen.add(lower_keyword)
    return unique_keywords

def validate_keywords(keywords: List[str], job_description: str) -> List[str]:
    """Validate and filter keywords based on job description."""
    job_description_lower = job_description.lower()
    validated_keywords = [kw for kw in keywords 
                          if kw.lower() in job_description_lower 
                          or is_contextually_implied(kw, job_description)]
    return validated_keywords

def is_contextually_implied(keyword: str, job_description: str) -> bool:
    """Check if a keyword is contextually implied in the job description."""
    # Implement your logic to determine contextual implication
    return True

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
    
    logger.debug(f"All Keywords: {all_keywords}")
    
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
        logger.error(f"Qwen failed, using YAKE: {e}")
        return yake_extraction(user_message)

def yake_extraction(text: str) -> Dict:
    """Fallback keyword extraction using YAKE."""
    yake_extractor = KeywordExtractor(top=20)
    yake_keywords = yake_extractor.extract_keywords(text)
    return {"keybert": [], "yake": [kw[0] for kw in yake_keywords]}

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
        except (ValueValueError, json.JSONDecodeError):
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
        except (ValueValueError, json.JSONDecodeError):
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

@log_error
def hybrid_extraction(jd_text: str) -> Dict:
    """Combine LLM and statistical extraction."""
    try:
        # Technical skills extraction
        tech_output = tech_extractor(jd_text)
        logger.debug(f"Tech Output: {tech_output}")
        tech_keywords = extract_tech_keywords(tech_output[0]['generated_text'])
        logger.debug(f"Tech Keywords: {tech_keywords}")
        
        # Contextual phrases extraction
        context_keywords = extract_contextual_phrases(jd_text)
        logger.debug(f"Context Keywords: {context_keywords}")
        
        # Merge results
        merged_keywords = merge_keywords(tech_keywords, context_keywords)
        logger.debug(f"Merged Keywords: {merged_keywords}")
        
        return deduplicate_keywords(merged_keywords)
    except Exception as e:
        logger.error(f"Error in hybrid_extraction, using fallback: {e}")
        return hybrid_fallback(jd_text)
