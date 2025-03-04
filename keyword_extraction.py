import re
from typing import List, Dict, Any
from langchain_community.llms import Qwen

def setup_qwen_model():
    """Initialize the Qwen model for keyword extraction."""
    try:
        qwen = Qwen(
            model_name="qwen1.5-7b-chat",
            temperature=0.3,  # Lower temperature for more consistent outputs
            top_p=0.9,
            max_tokens=512
        )
        return qwen
    except Exception as e:
        print(f"Error initializing Qwen model: {str(e)}")
        return None

def extract_keywords_from_job_description(job_description: str) -> list:
    # Dummy implementation for keyword extraction
    keywords = job_description.split()  # Replace with actual keyword extraction logic
    return keywords

def normalize_keywords_strictly(keywords: List[str]) -> List[str]:
    """
    Apply strict normalization and deduplication to keywords.
    Strip all qualifiers and reduce to core skill names.
    
    Args:
        keywords: List of extracted keywords
        
    Returns:
        Strictly normalized and deduplicated list of keywords
    """
    # Core technology mapping (lowercase key to preferred form value)
    tech_mapping = {
        "sql skills": "SQL",
        "sql": "SQL",
        "sql programming": "SQL",
        "sql databases": "SQL",
        "sql knowledge": "SQL",
        "python programming": "Python",
        "python skills": "Python",
        "python": "Python",
        "r programming": "R",
        "r skills": "R",
        "r": "R",
        "snowflake cloud platform": "Snowflake",
        "snowflake": "Snowflake",
        "metabase bi tool": "Metabase",
        "metabase": "Metabase",
        "amplitude analytics tool": "Amplitude",
        "amplitude": "Amplitude",
        "data engineering": "Data Engineering",
        "data engineer": "Data Engineering",
        "database work": "Database Management",
        "database management": "Database Management",
        "database": "Database Management",
        "machine learning": "Machine Learning",
        "ml": "Machine Learning",
        "artificial intelligence": "AI",
        "ai": "AI",
        "bi": "Business Intelligence",
        "business intelligence": "Business Intelligence",
        "data analysis": "Data Analysis",
        "data analytics": "Data Analysis",
        "data visualization": "Data Visualization",
        "data science": "Data Science",
        "javascript": "JavaScript",
        "js": "JavaScript",
        "typescript": "TypeScript",
        "java": "Java",
        "self-service tools": "Self-Service Tools",
        "self service tools": "Self-Service Tools",
        "self-service tools creation": "Self-Service Tools",
        "finance": "Finance",
        "financial analysis": "Financial Analysis",
        "financial planning": "Financial Planning",
        "financial reporting": "Financial Reporting",
        "capital markets": "Capital Markets"
    }
    
    # Qualifiers to strip away
    qualifiers = [
        "skills in", "skill in", "skills with", "skill with", 
        "experience in", "experience with", "experienced in", "experienced with",
        "knowledge of", "knowledge in", "proficiency in", "proficient in",
        "proficient with", "expertise in", "expert in", "familiar with",
        "familiarity with", "understanding of", "work with", "working with",
        "skills", "skill", "expertise", "knowledge", "ability to use",
        "ability to", "proficiency", "experience", "understanding",
        "demonstrated ability", "prior experience", "plus"
    ]
    
    # Result storage
    normalized_keywords = []
    seen_concepts = set()
    
    for kw in keywords:
        if not kw or not kw.strip():
            continue
        
        # Normalize whitespace and convert to lowercase for processing
        clean_kw = re.sub(r'\s+', ' ', kw.strip().lower())
        
        # Remove qualifiers
        for qualifier in qualifiers:
            # Remove qualifier from start
            if clean_kw.startswith(f"{qualifier} "):
                clean_kw = clean_kw[len(f"{qualifier} "):].strip()
            
            # Remove qualifier from end
            if clean_kw.endswith(f" {qualifier}"):
                clean_kw = clean_kw[:-len(f" {qualifier}")].strip()
        
        # Map to canonical form if available
        if clean_kw in tech_mapping:
            canonical = tech_mapping[clean_kw]
            if canonical.lower() not in seen_concepts:
                normalized_keywords.append(canonical)
                seen_concepts.add(canonical.lower())
        else:
            # For terms not in our mapping
            if clean_kw and clean_kw not in seen_concepts:
                # Capitalize properly
                if clean_kw.upper() in ["AWS", "GCP", "ETL", "API", "UI", "UX", "CI/CD"]:
                    normalized_keywords.append(clean_kw.upper())
                else:
                    normalized_keywords.append(" ".join(w.capitalize() for w in clean_kw.split()))
                seen_concepts.add(clean_kw)
    
    return normalized_keywords

def regex_extract_keywords(job_description: str, max_keywords: int = 15) -> List[str]:
    """
    Extract keywords using regex patterns as a fallback method.
    
    Args:
        job_description: The job description text
        max_keywords: Maximum number of keywords to extract
        
    Returns:
        List of extracted keywords
    """
    # Common technical skills and technologies pattern - updated with terms from the job description
    tech_pattern = r'\b(?:Python|Java|C\+\+|JavaScript|R\b|SQL|NoSQL|MongoDB|MySQL|PostgreSQL|AWS|Azure|GCP|Docker|Kubernetes|CI/CD|DevOps|Machine Learning|AI|NLP|Data Science|Data Analysis|Big Data|Hadoop|Spark|Excel|PowerBI|Tableau|REST|API|Git|Agile|Scrum|Cloud|Microservices|TensorFlow|PyTorch|Snowflake|Amplitude|Metabase|BI tool|Data Engineering|Database|Finance|Financial|Capital Markets)\b'
    
    # Extract technical skills
    tech_skills = re.findall(tech_pattern, job_description, re.IGNORECASE)
    
    # Extract phrases that look like requirements
    req_pattern = r'(?:proficient|experience|knowledge|skills|expertise|familiarity|ability) (?:in|with|of|to) ([^.;,]*)'
    requirement_matches = re.findall(req_pattern, job_description, re.IGNORECASE)
    requirement_phrases = [match.strip() for match in requirement_matches if len(match.strip()) > 3]
    
    # Combine all potential keywords
    all_keywords = tech_skills + requirement_phrases
    
    # Apply strict normalization and deduplication
    return normalize_keywords_strictly(all_keywords)[:max_keywords]

def process_extracted_categories(extracted_data: dict) -> List[str]:
    """
    Process extracted categories from Qwen's structured output format
    and return a unified, deduplicated list of keywords.
    
    Args:
        extracted_data: Dictionary with categorized keywords
        
    Returns:
        List of normalized and deduplicated keywords
    """
    all_keywords = []
    
    # Extract keywords from all categories
    for category, keywords in extracted_data.items():
        if isinstance(keywords, list):
            all_keywords.extend(keywords)
        elif isinstance(keywords, str):
            # Split comma-separated string into list
            all_keywords.extend([k.strip() for k in keywords.split(',')])
    
    # Apply strict normalization and deduplication
    return normalize_keywords_strictly(all_keywords)

def align_resume_with_job(resume_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
    """
    Process a job description and align a resume with extracted keywords.
    
    Args:
        resume_data: The candidate's resume data
        job_description: The job description text
        
    Returns:
        Resume data enhanced with job keywords
    """
    from rephrasing import enhance_resume_content
    
    # Extract keywords from job description
    job_keywords = extract_keywords_from_job_description(job_description)
    print(f"Extracted job keywords: {job_keywords}")
    
    # Store the job description and extracted keywords in resume_data
    resume_data['job_description'] = job_description
    resume_data['job_description_keywords'] = job_keywords
    
    # Enhance resume content with job keywords
    enhanced_resume = enhance_resume_content(resume_data, job_keywords)
    
    return enhanced_resume
