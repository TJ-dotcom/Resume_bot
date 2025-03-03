"""
Utility functions for handling and processing keywords
"""

from typing import Dict, List, Set, Any
import logging
import re

logger = logging.getLogger(__name__)

def deduplicate_keywords(keywords: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Remove duplicates from keyword categories while preserving order
    
    Args:
        keywords (dict): Dictionary of keyword categories
        
    Returns:
        dict: Dictionary with deduplicated keywords
    """
    result = {}
    for category, kw_list in keywords.items():
        # Create a case-insensitive set to track seen keywords
        seen = set()
        unique_keywords = []
        
        for kw in kw_list:
            # Skip empty or None values
            if not kw:
                continue
                
            # Normalize the keyword
            normalized = kw.lower().strip()
            
            # Skip if we've seen this before
            if normalized in seen:
                continue
                
            # Add to results and mark as seen
            unique_keywords.append(kw)
            seen.add(normalized)
            
        result[category] = unique_keywords
    
    return result

def normalize_keyword(keyword: str) -> str:
    """
    Normalize a keyword for better matching
    
    Args:
        keyword (str): The keyword to normalize
        
    Returns:
        str: Normalized keyword
    """
    # Remove special characters, extra spaces, and convert to lowercase
    normalized = re.sub(r'[^\w\s]', '', keyword.lower()).strip()
    return normalized

def are_keywords_similar(kw1: str, kw2: str, similarity_threshold: float = 0.8) -> bool:
    """
    Check if two keywords are similar using fuzzy matching
    
    Args:
        kw1 (str): First keyword
        kw2 (str): Second keyword
        similarity_threshold (float): Threshold for considering keywords similar
        
    Returns:
        bool: True if keywords are similar, False otherwise
    """
    # Simple containment check
    if kw1.lower() in kw2.lower() or kw2.lower() in kw1.lower():
        return True
        
    # Check for exact match after normalization
    if normalize_keyword(kw1) == normalize_keyword(kw2):
        return True
        
    # Check for high word overlap in multi-word phrases
    kw1_words = set(normalize_keyword(kw1).split())
    kw2_words = set(normalize_keyword(kw2).split())
    
    if kw1_words and kw2_words:  # Ensure non-empty sets
        # Calculate Jaccard similarity
        intersection = len(kw1_words.intersection(kw2_words))
        union = len(kw1_words.union(kw2_words))
        
        if union > 0 and intersection / union >= similarity_threshold:
            return True
    
    return False

def merge_similar_keywords(keywords: List[str]) -> List[str]:
    """
    Merge similar keywords into a single representative keyword
    
    Args:
        keywords (list): List of keywords
        
    Returns:
        list: List with merged similar keywords
    """
    if not keywords:
        return []
        
    # Start with the first keyword
    result = [keywords[0]]
    
    # Check each keyword against the result list
    for kw in keywords[1:]:
        # Skip if the keyword is similar to any in the result
        if any(are_keywords_similar(kw, existing) for existing in result):
            continue
            
        # Add if it's a new unique keyword
        result.append(kw)
    
    return result

def process_keywords(keywords: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Process keywords by deduplicating and merging similar ones
    
    Args:
        keywords (dict): Dictionary of keyword categories
        
    Returns:
        dict: Processed keywords
    """
    # First deduplicate
    deduped = deduplicate_keywords(keywords)
    
    # Then merge similar keywords within each category
    result = {}
    for category, kw_list in deduped.items():
        result[category] = merge_similar_keywords(kw_list)
        
    return result

def extract_skills_from_text(text: str) -> List[str]:
    """
    Extract skills/keywords from a text using simple heuristics
    
    Args:
        text (str): Text to extract skills from
        
    Returns:
        list: Extracted skills
    """
    # Split text into potential skill phrases
    words = re.findall(r'\b[A-Za-z][\w\+\#\-\.\s]*[A-Za-z0-9]\b', text)
    
    # Filter likely skills (typically 1-4 words)
    skills = []
    for word in words:
        word = word.strip()
        if 2 <= len(word) <= 30 and len(word.split()) <= 4:
            skills.append(word)
            
    # De-duplicate
    seen = set()
    unique_skills = []
    for skill in skills:
        normalized = normalize_keyword(skill)
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique_skills.append(skill)
            
    return unique_skills

def categorize_keywords(keywords: List[str]) -> Dict[str, List[str]]:
    """
    Attempt to categorize a flat list of keywords into categories
    
    Args:
        keywords (list): List of keywords to categorize
        
    Returns:
        dict: Categorized keywords
    """
    # Simple rule-based categorization
    categories = {
        "technical_skills": [],
        "soft_skills": [],
        "cloud_technologies": [],
        "programming_knowledge": []
    }
    
    # Keywords that typically belong to specific categories
    cloud_keywords = {'aws', 'azure', 'gcp', 'cloud', 'serverless', 'lambda', 'ec2', 's3', 'dynamodb', 
                     'cosmos', 'firebase', 'cloudflare', 'kubernetes', 'docker', 'snowflake'}
                     
    programming_keywords = {'python', 'java', 'javascript', 'c++', 'ruby', 'php', 'sql', 'nosql', 
                           'programming', 'coding', 'algorithm', 'data structure', 'api'}
                           
    soft_skills = {'communication', 'leadership', 'teamwork', 'collaboration', 'problem solving',
                  'creativity', 'adaptability', 'time management', 'critical thinking', 
                  'attention to detail', 'organization', 'flexibility'}
    
    for kw in keywords:
        kw_lower = kw.lower()
        
        # Check if belongs to cloud technologies
        if any(cloud_word in kw_lower for cloud_word in cloud_keywords):
            categories["cloud_technologies"].append(kw)
            
        # Check if belongs to programming knowledge
        elif any(prog_word in kw_lower for prog_word in programming_keywords):
            categories["programming_knowledge"].append(kw)
            
        # Check if belongs to soft skills
        elif any(soft_word in kw_lower for soft_word in soft_skills):
            categories["soft_skills"].append(kw)
            
        # Default to technical skills
        else:
            categories["technical_skills"].append(kw)
    
    return categories
