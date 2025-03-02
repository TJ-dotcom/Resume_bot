import requests
import logging
import time
import json
import os

logger = logging.getLogger(__name__)

# Set the DeepSeek model endpoint
deepseek_endpoint = 'http://127.0.0.1:1234/v1/completions'
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

def generate_deepseek_response(prompt):
    """
    Generate a response using the DeepSeek API
    
    Args:
        prompt (str): The prompt to send to DeepSeek
        
    Returns:
        str: The generated response text
    """
    if not DEEPSEEK_API_KEY:
        logger.warning("Deepseek API key not configured, returning empty response")
        return ""
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 1000
        }
        
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data)
        response.raise_for_status()
        
        return response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        
    except Exception as e:
        logger.error(f"Error generating response from Deepseek: {e}")
        return ""

def extract_keywords_with_deepseek(job_description):
    """
    Extract keywords from a job description using DeepSeek API.
    Only extracts keywords that actually appear in the job description,
    except for categories with zero keywords where minimal fallbacks are provided.
    
    Args:
        job_description (str): The job description text
        
    Returns:
        dict: Dictionary containing extracted keywords by category
    """
    if not job_description:
        logger.warning("Empty job description provided")
        return {"technical_skills": [], "soft_skills": [], "domain_knowledge": [], "qualifications": []}
    
    try:
        # Construct prompt for keyword extraction
        prompt = f"""
        Extract the most important keywords from this job description, categorized into:
        1. Technical skills
        2. Soft skills
        3. Domain knowledge
        4. Qualifications/certifications
        
        Job Description:
        {job_description}
        
        Format your response as a JSON object with these categories as keys and lists of keywords as values.
        """
        
        # Get response from Deepseek
        response = generate_deepseek_response(prompt)
        
        # Parse JSON from response
        try:
            # First try to parse the entire response as JSON
            keywords = json.loads(response)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON from the response text
            try:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    keywords = json.loads(response[json_start:json_end])
                else:
                    raise ValueError("No valid JSON found in response")
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse keywords from response: {e}")
                return {"technical_skills": [], "soft_skills": [], "domain_knowledge": [], "qualifications": []}
        
        # Ensure the expected categories exist
        expected_categories = ["technical_skills", "soft_skills", "domain_knowledge", "qualifications"]
        for category in expected_categories:
            if category not in keywords:
                keywords[category] = []
            # Ensure each category contains a list
            if not isinstance(keywords[category], list):
                keywords[category] = []
        
        return keywords
        
    except Exception as e:
        logger.error(f"Error extracting keywords with Deepseek: {e}")
        return {"technical_skills": [], "soft_skills": [], "domain_knowledge": [], "qualifications": []}

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
