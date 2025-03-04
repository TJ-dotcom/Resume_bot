import requests
import logging
import time
import json
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)
QWEN_MODEL = "qwen2.5-7b-instruct-1m"
# Set the QWEN model endpoint
QWEN_API_URL = "http://127.0.0.1:1234/v1/chat/completions"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

def generate_qwen_response(prompt):
    """
    Generate a response using the QWEN API
    
    Args:
        prompt (str): The prompt to send to QWEN
        
    Returns:
        str: The generated response text
    """
    try:
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "model": QWEN_MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 1000
        }
        
        logger.info(f"Sending request to QWEN API with prompt: {prompt}")
        response = requests.post(QWEN_API_URL, headers=headers, json=data)
        response.raise_for_status()
        
        response_text = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        logger.info(f"Received response from QWEN API: {response_text}")
        
        return response_text
        
    except Exception as e:
        logger.error(f"Error generating response from QWEN: {e}")
        return ""

def extract_keywords_with_qwen(job_description: str) -> Dict[str, Any]:
    """Extract keywords from job description using Qwen model."""
    url = "http://127.0.0.1:1234/v1/completions"  # Ensure this is the correct endpoint
    payload = {
        "model": "qwen2.5-7b-instruct-1m",
        "prompt": job_description,
        "temperature": 0.3,
        "top_p": 0.9,
        "max_tokens": 512
    }
    try:
        logger.info(f"Sending request to Qwen API with payload: {payload}")
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Received response from Qwen API: {data}")
        
        # Extract keywords from the response
        keywords = data.get('keywords', {})
        logger.info(f"Extracted keywords before deduplication: {keywords}")
        
        # Remove duplicates
        for category in keywords:
            original_list = keywords[category]
            keywords[category] = list(set(keywords[category]))
            logger.info(f"Category '{category}' - Original: {original_list}, Deduplicated: {keywords[category]}")
        
        logger.info(f"Final extracted keywords: {keywords}")
        return keywords
    except Exception as e:
        logger.error(f"Error extracting keywords with Qwen model: {str(e)}")
        return {}

def infuse_keywords(sections, keywords):
    """
    Intelligently infuse keywords into the resume sections
    
    Args:
        sections (dict): Resume sections dictionary
        keywords (dict): Extracted keywords by category
        
    Returns:
        dict: Updated resume sections with carefully infused keywords
    """
    # Only add skills that don't already exist in the skills section
    if "skills" in sections and isinstance(sections["skills"], list):
        existing_skills = [skill.lower() for skill in sections["skills"]]
        
        # Create categories to prioritize
        priority_categories = [
            "technical_skills", 
            "programming_languages", 
            "technical_tools", 
            "data_tools", 
            "cloud_technologies", 
            "soft_skills"
        ]
        
        # Add skills based on priority categories
        for category in priority_categories:
            if category in keywords:
                for skill in keywords[category]:
                    # Check if the skill or a similar one already exists
                    if skill.lower() not in existing_skills and not any(
                        skill.lower() in existing.lower() or existing.lower() in skill.lower() 
                        for existing in sections["skills"]
                    ):
                        sections["skills"].append(skill)
                        existing_skills.append(skill.lower())
    
    logger.info(f"Updated skills section with new keywords. Total skills: {len(sections.get('skills', []))}")
    return sections

def rephrase_and_tailor_resume(sections, keywords, job_description):
    """
    Rephrase and tailor resume sections using DeepSeek API
    following specific guidelines for each section.
    
    Args:
        sections (dict): Resume sections dictionary
        keywords (dict): Extracted keywords by category
        job_description (str): Job description to tailor for
        
    Returns:
        dict: Tailored resume sections
    """
    # Flatten keywords for easier reference
    all_keywords = []
    for category, kw_list in keywords.items():
        all_keywords.extend(kw_list)
    
    # Remove duplicates while preserving order
    unique_keywords = []
    for kw in all_keywords:
        if kw not in unique_keywords:
            unique_keywords.append(kw)
    
    all_keywords_str = ", ".join(unique_keywords)
    
    # Main tailoring instructions that will be included in all prompts
    tailoring_instructions = """
You are a professional resume expert tasked with enhancing resume content to match job requirements.

IMPORTANT GUIDELINES:
1. DO NOT add, remove, or modify company names, role names, or project names.
2. DO incorporate keywords naturally where they fit - don't force them where they don't belong.
3. DO focus on enhancing the candidate's contributions and achievements.
4. DO maintain professionalism and clarity at all times.
5. DO ensure the content reflects the candidate's actual experience.
6. DO prioritize relevance and impact when selecting keywords to include.
7. DO make substantial, meaningful changes to the content.
8. DO be specific and quantitative when possible (e.g., add metrics, numbers, percentages).

Your goal is to make the resume content more aligned with the job description while preserving its authenticity.
"""
    
    for section in ['skills', 'experience', 'projects']:
        if section in sections:
            for i, line in enumerate(sections[section]):
                try:
                    # Skip tailoring the skills section, as it's handled by infuse_keywords
                    if section == 'skills':
                        continue
                        
                    elif section == 'experience':
                        # Preserve company name and role name
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            role_company, description = parts
                            prompt = tailoring_instructions + f"""
### JOB DESCRIPTION ###
{job_description}

### CURRENT EXPERIENCE ENTRY ###
Role/Company: {role_company}
Description: {description}

### KEYWORDS TO INCORPORATE (where appropriate) ###
{all_keywords_str}

### INSTRUCTIONS ###
1. DO NOT modify the Role/Company name: "{role_company}"
2. Rewrite ONLY the description part to incorporate relevant keywords
3. Enhance the description to showcase accomplishments and relevant skills
4. Be specific and impactful
5. Ensure the content is substantially improved and tailored to the job

### TAILORED DESCRIPTION (write only the description, not the role/company) ###
"""
                            tailored_description = generate_deepseek_response(prompt)
                            if tailored_description:
                                sections[section][i] = f"{role_company}: {tailored_description}"
                            
                    elif section == 'projects':
                        # Preserve project names
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            project_name, details = parts
                            prompt = tailoring_instructions + f"""
### JOB DESCRIPTION ###
{job_description}

### CURRENT PROJECT ENTRY ###
Project Name: {project_name}
Description: {details}

### KEYWORDS TO INCORPORATE (where appropriate) ###
{all_keywords_str}

### INSTRUCTIONS ###
1. DO NOT modify the Project Name: "{project_name}"
2. Rewrite ONLY the description part to incorporate relevant keywords
3. Enhance the description to showcase technical skills and accomplishments
4. Be specific about technologies used and outcomes achieved
5. Ensure the content is substantially improved and tailored to the job

### TAILORED DESCRIPTION (write only the description, not the project name) ###
"""
                            tailored_details = generate_deepseek_response(prompt)
                            if tailored_details:
                                sections[section][i] = f"{project_name}: {tailored_details}"
                            
                except Exception as e:
                    logger.error(f"Error tailoring section {section}, entry {i}: {e}", exc_info=True)
                    # Keep original content if there's an error
                    pass
                    
    return sections

"""
Utility functions for resume-bot processing.
"""

import logging
import os
import requests
import json
from typing import Dict, List, Any
import traceback

# Get logger for this module
logger = logging.getLogger(__name__)

# DeepSeek API configuration
DEEPSEEK_API_URL = "http://127.0.0.1:1234/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-r1-distill-qwen-7b"

def log_error(func):
    """Decorator to log errors in functions."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            logger.error(traceback.format_exc())
            raise
    return wrapper

@log_error
def extract_keywords_with_deepseek(job_description: str) -> Dict[str, List[str]]:
    """
    Extract keywords from job description using DeepSeek LLM.
    Extracts ALL relevant keywords without duplications.
    
    Args:
        job_description (str): The job description text
        
    Returns:
        dict: Dictionary of keyword categories and lists
    """
    system_prompt = """
    You are a job analysis expert. Extract ALL skills, requirements, and qualifications 
    from the provided job description.
    
    Organize them into the following categories:
    1. technical_skills: Technical skills, tools, platforms, databases
    2. soft_skills: Communication skills, teamwork abilities, leadership traits, work style characteristics
    3. cloud_technologies: Cloud platforms, services, and related technologies
    4. programming_knowledge: Programming languages, concepts, paradigms, and specific technical knowledge areas
    
    IMPORTANT RULES:
    - Remove all duplicate keywords within each category
    - Each keyword should appear exactly once
    - Format each keyword as a simple phrase (1-4 words typically)
    - If a category has no explicitly mentioned keywords, identify implied ones that would be relevant
    
    Return your response as a JSON object with these categories as keys and arrays of non-duplicate keywords as values.
    """
    
    try:
        response = call_deepseek_api(system_prompt, job_description)
        
        # Extract JSON from response
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        keywords = extract_json_from_text(content)
        
        # Validate and ensure all expected categories exist
        expected_categories = ["technical_skills", "soft_skills", "cloud_technologies", "programming_knowledge"]
        for category in expected_categories:
            if category not in keywords:
                keywords[category] = []
            else:
                # Ensure no duplicates (case-insensitive)
                processed_keywords = []
                seen = set()
                for kw in keywords[category]:
                    if kw.lower() not in seen:
                        seen.add(kw.lower())
                        processed_keywords.append(kw)
                keywords[category] = processed_keywords
        
        return keywords
    
    except Exception as e:
        logger.error(f"Error extracting keywords with DeepSeek: {e}")
        # Return empty structure as fallback
        return {
            "technical_skills": [],
            "soft_skills": [],
            "cloud_technologies": [],
            "programming_knowledge": []
        }

@log_error
def generate_deepseek_response(prompt: str) -> str:
    """
    Generate text using DeepSeek LLM.
    
    Args:
        prompt (str): The prompt to send to DeepSeek
        
    Returns:
        str: Generated response text
    """
    system_prompt = "You are an AI assistant specialized in resume enhancement and job applications."
    
    try:
        response = call_deepseek_api(system_prompt, prompt)
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        return content
    
    except Exception as e:
        logger.error(f"Error generating text with DeepSeek: {e}")
        return ""

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
    if "skills" in sections:
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
    
    # Enhance summary with relevant keywords if it exists
    if "summary" in sections and sections["summary"]:
        # Build a de-duplicated string of all keywords
        unique_keywords = []
        all_seen = set()
        for category in keywords.values():
            for kw in category:
                if kw.lower() not in all_seen:
                    all_seen.add(kw.lower())
                    unique_keywords.append(kw)
                    
        all_keywords_str = ", ".join(unique_keywords)
        
        # Use DeepSeek/Qwen to rewrite the summary with infused keywords
        prompt = f"""
        Enhance the following resume summary by incorporating relevant keywords: 
        {all_keywords_str}
        
        Original summary:
        {sections['summary']}
        
        Make sure to include relevant keywords naturally while keeping the summary coherent.
        Provide only the enhanced summary.
        """
        enhanced_summary = generate_deepseek_response(prompt).strip()
        if enhanced_summary:  # Only update if we got something back
            sections["summary"] = enhanced_summary
    
    logger.info(f"Updated skills section with unique keywords. Total skills: {len(sections.get('skills', []))}")
    return sections

@log_error
def rephrase_and_tailor_resume(sections: Dict, keywords: Dict[str, List[str]], job_description: str) -> Dict:
    """
    Rephrase and tailor resume sections to match job description.
    
    Args:
        sections (dict): Resume sections
        keywords (dict): Extracted keywords from job description
        job_description (str): The job description
        
    Returns:
        dict: Tailored resume sections
    """
    # Create a combined list of keywords for reference
    all_keywords = []
    for category, kws in keywords.items():
        all_keywords.extend(kws)
    
    # Extract job title and core requirements for better tailoring
    job_title = extract_job_title(job_description)
    
    # Tailor experience section
    if "experience" in sections and sections["experience"]:
        tailored_experience = []
        
        for exp_entry in sections["experience"]:
            # For each experience entry, tailor it to highlight relevant skills
            prompt = f"""
            Rewrite the following resume experience bullet point to better match this job: {job_title}
            
            Highlight these keywords: {', '.join(all_keywords)}
            
            Original experience:
            {exp_entry}
            
            Provide only the improved version with the same or similar length. Maintain factual accuracy.
            """
            
            tailored_entry = generate_qwen_response(prompt).strip()
            # Only use the tailored version if we got a valid response
            tailored_experience.append(tailored_entry if tailored_entry else exp_entry)
        
        sections["experience"] = tailored_experience
    
    # Similarly, tailor projects section
    if "projects" in sections and sections["projects"]:
        # Similar approach for projects
        tailored_projects = []
        
        for project_entry in sections["projects"]:
            prompt = f"""
            Rewrite the following project description to better highlight skills relevant to: {job_title}
            
            Focus on these keywords: {', '.join(all_keywords)}
            
            Original project:
            {project_entry}
            
            Provide only the improved version with the same or similar length. Maintain factual accuracy.
            """
            
            tailored_entry = generate_qwen_response(prompt).strip()
            tailored_projects.append(tailored_entry if tailored_entry else project_entry)
        
        sections["projects"] = tailored_projects
    
    return sections

@log_error
def extract_job_title(job_description: str) -> str:
    """Extract job title from job description."""
    # Simple heuristic - often the job title is in the first few lines
    first_lines = job_description.split("\n")[:3]
    for line in first_lines:
        if len(line.strip()) > 0 and len(line.strip().split()) <= 5:
            return line.strip()
    
    # Fallback - ask DeepSeek to extract it
    prompt = f"Extract only the job title from this job description:\n\n{job_description}"
    system_prompt = "You are a job analysis expert. Extract only the job title from the description."
    
    try:
        response = call_deepseek_api(system_prompt, prompt)
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        return content.strip()
    except Exception:
        # Final fallback
        return "the position"

@log_error
def call_deepseek_api(system_prompt: str, user_message: str) -> Dict:
    """
    Make an API call to the local DeepSeek server.
    
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
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.2,
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to DeepSeek API: {e}")
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
    logger.warning("Could not extract JSON from DeepSeek response")
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
def extract_keywords_with_qwen(job_description: str) -> Dict[str, List[str]]:
    """
    Extract keywords from job description using Qwen model.
    Extracts ALL relevant keywords without duplications.
    
    Args:
        job_description (str): The job description text
        
    Returns:
        dict: Dictionary of keyword categories and lists
    """
    system_prompt = """
    You are a job analysis expert. Extract ALL TOP 5-7 keywords for skills, requirements, and qualifications 
    from the provided job description.
    
    Organize them into the following categories:
    1. technical_skills: Technical skills, tools, platforms, databases, (DO NOT include programming languages here)
    2. soft_skills: identify Cognitive skills, work style, Communication skills, teamwork abilities, leadership traits, work style characteristics (identify atleast 5 soft skills from the provided job description)
    3. cloud_technologies: Cloud platforms, services, and related technologies
    4. programming_knowledge: Programming languages, concepts, paradigms, and specific technical knowledge areas
    
    IMPORTANT RULES:
    - Do not invent or infer any additional keywords
    - IDENTIFY ALL POTENTIAL KEYWORDS:
    - Technical tools/platforms (e.g., Snowflake, Metabase)
    - Methodologies (e.g., Agile, Scrum)
    - Domain knowledge (e.g., FP&A, HIPAA)
    - Soft skills (e.g., Communication, Leadership)
    - Implied skills from context (e.g., "optimize data collection" → Process Automation)
    - Remove all duplicate keywords within each category
    - Each keyword should appear exactly once
    - Format each keyword as a simple phrase 
    - If a category has no explicitly mentioned keywords, identify implied ones that would be relevant
    - 
    
    Return your response as a JSON object with these categories as keys and arrays of non-duplicate keywords as values.
    """
    
    try:
        response = call_qwen_api(system_prompt, job_description)
        
        # Extract JSON from response
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        logger.info(f"Qwen API response: {content}")
        keywords = extract_json_from_text(content)
        
        # Validate and ensure all expected categories exist
        expected_categories = ["technical_skills", "soft_skills", "cloud_technologies", "programming_knowledge"]
        for category in expected_categories:
            if category not in keywords:
                keywords[category] = []
            else:
                # Ensure no duplicates (case-insensitive)
                processed_keywords = []
                seen = set()
                for kw in keywords[category]:
                    if kw.lower() not in seen:
                        seen.add(kw.lower())
                        processed_keywords.append(kw)
                keywords[category] = processed_keywords
        
        # Remove programming languages from technical_skills
        programming_languages = set(keywords.get("programming_knowledge", []))
        keywords["technical_skills"] = [kw for kw in keywords["technical_skills"] if kw not in programming_languages]
        
        # Verify that extracted keywords are present in the job description
        job_description_lower = job_description.lower()
        for category in keywords:
            keywords[category] = [kw for kw in keywords[category] if kw.lower() in job_description_lower]
        
        logger.info(f"Final extracted keywords: {keywords}")
        return keywords
    
    except Exception as e:
        logger.error(f"Error extracting keywords with Qwen: {e}")
        # Return empty structure as fallback
        return {
            "technical_skills": [],
            "soft_skills": [],
            "cloud_technologies": [],
            "programming_knowledge": []
        }

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
