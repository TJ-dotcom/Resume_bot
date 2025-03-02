import requests
import logging
import time

logger = logging.getLogger(__name__)

# Set the DeepSeek model endpoint
deepseek_endpoint = 'http://127.0.0.1:1234/v1/completions'

def generate_deepseek_response(prompt):
    """
    Generate a response using the DeepSeek API
    
    Args:
        prompt (str): The prompt to send to DeepSeek
        
    Returns:
        str: The generated response text
    """
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
    """
    Extract keywords from a job description using DeepSeek API
    
    Args:
        job_description (str): The job description text
        
    Returns:
        dict: Dictionary containing extracted keywords by category
    """
    # Define fallback keywords in case of API failure
    fallback_keywords = {
        "technical_skills": ["Data Analysis", "Software Development", "Project Management", "Database Management", "API Integration"],
        "soft_skills": ["Communication", "Teamwork", "Problem Solving", "Critical Thinking", "Adaptability"],
        "programming_languages": ["Python", "JavaScript", "Java", "SQL", "C++"],
        "technical_tools": ["Git", "Docker", "Kubernetes", "VS Code", "Jira"],
        "data_tools": ["Excel", "Tableau", "Power BI", "SQL Server", "MongoDB"],
        "cloud_technologies": ["AWS", "Azure", "Google Cloud", "Heroku", "Docker"]
    }
    
    # If job description is too short, use fallback keywords
    if len(job_description) < 20:
        logger.warning(f"Job description too short: {job_description}. Using fallback keywords.")
        return fallback_keywords
    
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
        f"Provide the top 5-7 keywords for each category in the following format:\n"
        f"Technical Skills: skill1, skill2, ...\n"
        f"Soft Skills: skill1, skill2, ...\n"
        f"Programming Languages: language1, language2, ...\n"
        f"Technical Tools: tool1, tool2, ...\n"
        f"Data Tools: tool1, tool2, ...\n"
        f"Cloud Technologies: technology1, technology2, ...\n"
        f"If a category has no relevant items in the description, provide at least 2-3 general items that might be useful."
    )
    
    # Log the prompt for debugging
    logger.info(f"Sending keyword extraction prompt to DeepSeek. Job desc length: {len(job_description)}")
    
    response = generate_deepseek_response(prompt)
    logger.info(f"DeepSeek keyword extraction response: {response}")
    
    if not response or len(response) < 10:
        logger.error(f"Empty or very short response from DeepSeek API. Using fallback keywords.")
        return fallback_keywords
    
    try:
        # Parse the response to extract keywords
        lines = response.split('\n')
        keywords = {
            "technical_skills": [],
            "soft_skills": [],
            "programming_languages": [],
            "technical_tools": [],
            "data_tools": [],
            "cloud_technologies": []
        }
        
        # Process each line to extract keywords
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Process each category
            if line.startswith("Technical Skills:"):
                skills = [s.strip() for s in line[len("Technical Skills:"):].split(',')]
                keywords["technical_skills"] = [s for s in skills if s]
                
            elif line.startswith("Soft Skills:"):
                skills = [s.strip() for s in line[len("Soft Skills:"):].split(',')]
                keywords["soft_skills"] = [s for s in skills if s]
                
            elif line.startswith("Programming Languages:"):
                langs = [s.strip() for s in line[len("Programming Languages:"):].split(',')]
                keywords["programming_languages"] = [s for s in langs if s]
                
            elif line.startswith("Technical Tools:"):
                tools = [s.strip() for s in line[len("Technical Tools:"):].split(',')]
                keywords["technical_tools"] = [s for s in tools if s]
                
            elif line.startswith("Data Tools:"):
                data_tools = [s.strip() for s in line[len("Data Tools:"):].split(',')]
                keywords["data_tools"] = [s for s in data_tools if s]
                
            elif line.startswith("Cloud Technologies:"):
                cloud_tech = [s.strip() for s in line[len("Cloud Technologies:"):].split(',')]
                keywords["cloud_technologies"] = [s for s in cloud_tech if s]
        
        # Ensure each category has at least some keywords by using fallbacks if needed
        for category in keywords:
            if not keywords[category]:
                keywords[category] = fallback_keywords[category]
            # Limit to 7 keywords per category
            keywords[category] = keywords[category][:7] if len(keywords[category]) > 7 else keywords[category]
        
        logger.info(f"Successfully extracted keywords: {keywords}")
        return keywords
    
    except Exception as e:
        logger.error(f"Error parsing DeepSeek response: {e}", exc_info=True)
        return fallback_keywords

def infuse_keywords(sections, keywords):
    """
    Intelligently infuse keywords into the resume sections
    
    Args:
        sections (dict): Resume sections dictionary
        keywords (dict): Extracted keywords by category
        
    Returns:
        dict: Updated resume sections with carefully infused keywords
    """
    # Only add technical skills that don't already exist in the skills section
    if "skills" in sections and isinstance(sections["skills"], list):
        existing_skills = [skill.lower() for skill in sections["skills"]]
        
        # Add technical skills if not already present
        for skill in keywords["technical_skills"]:
            if skill.lower() not in existing_skills:
                sections["skills"].append(skill)
                existing_skills.append(skill.lower())
        
        # Add programming languages if not already present
        for lang in keywords["programming_languages"]:
            if lang.lower() not in existing_skills:
                sections["skills"].append(lang)
                existing_skills.append(lang.lower())
                
        # Add technical tools if not already present
        for tool in keywords["technical_tools"]:
            if tool.lower() not in existing_skills:
                sections["skills"].append(tool)
                existing_skills.append(tool.lower())
    
    # No longer blindly adding keywords to experience and projects sections
    # These will be handled more intelligently in rephrase_and_tailor_resume
    
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
                            prompt = (
                                f"Rephrase the following experience description to incorporate relevant keywords naturally.\n\n"
                                f"### GUIDELINES ###\n"
                                f"- DO NOT modify the company name or role name\n"
                                f"- Incorporate the keywords naturally where they fit\n"
                                f"- Maintain professionalism and clarity\n"
                                f"- Focus on the candidate's contributions and achievements\n"
                                f"- Only use keywords that are relevant to this experience\n\n"
                                
                                f"### JOB DESCRIPTION ###\n{job_description}\n\n"
                                
                                f"### CURRENT DESCRIPTION ###\n{description}\n\n"
                                
                                f"### KEYWORDS TO INCORPORATE (where relevant) ###\n{all_keywords_str}\n\n"
                                
                                f"### REPHRASED DESCRIPTION ###\n"
                            )
                            tailored_description = generate_deepseek_response(prompt)
                            sections[section][i] = f"{role_company}: {tailored_description}"
                            
                    elif section == 'projects':
                        # Preserve project names
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            project_name, details = parts
                            prompt = (
                                f"Rephrase the following project description to incorporate relevant keywords naturally.\n\n"
                                f"### GUIDELINES ###\n"
                                f"- DO NOT modify the project name\n"
                                f"- Incorporate the keywords naturally where they fit\n"
                                f"- Maintain professionalism and clarity\n"
                                f"- Focus on the candidate's contributions and achievements\n"
                                f"- Only use keywords that are relevant to this project\n\n"
                                
                                f"### JOB DESCRIPTION ###\n{job_description}\n\n"
                                
                                f"### CURRENT DESCRIPTION ###\n{details}\n\n"
                                
                                f"### KEYWORDS TO INCORPORATE (where relevant) ###\n{all_keywords_str}\n\n"
                                
                                f"### REPHRASED DESCRIPTION ###\n"
                            )
                            tailored_details = generate_deepseek_response(prompt)
                            sections[section][i] = f"{project_name}: {tailored_details}"
                            
                except Exception as e:
                    logger.error(f"Error tailoring section {section}, entry {i}: {e}", exc_info=True)
                    # Keep original content if there's an error
                    pass
                    
    return sections
