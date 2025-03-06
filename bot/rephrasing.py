import json
import requests
from typing import Dict, List, Any
import os
from dotenv import load_dotenv
import re
from sentence_transformers import SentenceTransformer
import numpy as np
import logging

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    """Clean up the text by removing special characters and unwanted characters."""
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with a single space
    text = re.sub(r'[^\w\s,.]', '', text)  # Remove special characters except for word characters, spaces, commas, and periods
    return text.strip()

def remove_duplicate_sentences(text: str) -> str:
    """Remove duplicate sentences while preserving order."""
    sentences = text.split('. ')
    seen = set()
    unique = []
    for sent in sentences:
        clean_sent = sent.strip().lower()
        if clean_sent and clean_sent not in seen:
            seen.add(clean_sent)
            unique.append(sent)
    return '. '.join(unique).replace('..', '.')

def semantic_deduplication(text: str, threshold=0.85) -> str:
    """Advanced deduplication using sentence embeddings."""
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    sentences = [s.strip() for s in text.split('. ') if s]
    embeddings = model.encode(sentences)
    
    unique = []
    seen_embeddings = []
    for i, sent in enumerate(sentences):
        if not any(np.dot(embeddings[i], seen) > threshold for seen in seen_embeddings):
            unique.append(sent)
            seen_embeddings.append(embeddings[i])
    return '. '.join(unique)

def rephrase_text(prompt: str) -> str:
    """Rephrase text using the Mistral model hosted locally."""
    url = "http://127.0.0.1:1234/v1/completions"  # Local server address
    payload = {
        "model": "qwen2.5-7b-instruct-1m",
        "prompt": prompt,
        "temperature": 0.3,
        "top_p": 0.9,
        "max_tokens": 400,
        "frequency_penalty": 2.0,
        "presence_penalty": 1.2,
        "repetition_penalty": 2.2,
        "typical_p": 0.92,
        "top_k": 40
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        rephrased_text = data.get('choices', [{}])[0].get('text', '').strip()
        rephrased_text = clean_text(rephrased_text)  # Clean up the rephrased text
        rephrased_text = remove_duplicate_sentences(rephrased_text)  # Remove duplicate sentences
        rephrased_text = semantic_deduplication(rephrased_text)  # Advanced deduplication
        print(f"Payload: {json.dumps(payload, indent=2)}")  # Debug payload
        print(f"Response: {json.dumps(data, indent=2)}")  # Debug response
        return rephrased_text
    except Exception as e:
        print(f"Error rephrasing text with Mistral model: {str(e)}")
        return prompt

def rephrase_work_experience(experience_list: List[Dict[str, Any]], job_keywords: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    rephrased_experience = []
    used_keywords = set()
    
    for exp in experience_list:
        company = exp.get('company', '')
        position = exp.get('position', '')
        responsibilities = exp.get('responsibilities', [])
        if isinstance(responsibilities, str):
            responsibilities = [responsibilities]
        
        if not responsibilities:
            rephrased_experience.append(exp)
            continue
        
        print(f"Rephrasing experience for {company}, position: {position}")
        print(f"Using job keywords: {job_keywords}")
        
        rephrased_responsibilities = []
        for resp in responsibilities:
            available_keywords = [kw for kw in job_keywords if kw not in used_keywords]
            prompt = f"""
            You are an expert resume writer helping a candidate tailor their resume to a specific job.
            Rephrase the following job responsibility to align with the target job description keywords.
            
            Target job keywords: {', '.join(available_keywords)}
            
            Original responsibility: {resp}
            
            Your task:
            1. Incorporate at least 1-2 job keywords naturally where appropriate
            2. Emphasize relevant skills and achievements
            3. Use action verbs and quantifiable results
            4. Maintain professional resume language
            5. Keep approximately the same length as the original
            
            Additional constraints:
            - Avoid repeating any technical terms more than twice per section
            - Never use the same sentence structure consecutively
            - Vary action verbs between 'developed', 'engineered', 'implemented', etc.
            - Ensure 30% lexical diversity compared to original content
            
            Return ONLY the rephrased version with no explanations, quotes, or additional text.
            """
            
            try:
                rephrased_resp = rephrase_text(prompt)
                rephrased_resp = semantic_deduplication(rephrased_resp)
                print(f"Original: {resp}\nRephrased: {rephrased_resp}\n")
                rephrased_responsibilities.append(rephrased_resp)
                
                # Track used keywords
                for kw in available_keywords:
                    if kw in rephrased_resp:
                        used_keywords.add(kw)
            except Exception as e:
                print(f"Error rephrasing responsibility for {company}: {str(e)}")
                rephrased_responsibilities.append(resp)
        
        rephrased_exp = exp.copy()
        rephrased_exp['responsibilities'] = rephrased_responsibilities
        rephrased_experience.append(rephrased_exp)
    
    return rephrased_experience

def rephrase_projects(projects: List[Dict[str, Any]], job_keywords: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    rephrased_projects = []
    used_keywords = set()
    
    for project in projects:
        title = project.get('title', '')
        description = project.get('description', '')
        
        if not description:
            rephrased_projects.append(project)
            continue
            
        print(f"Rephrasing project: {title}")
        print(f"Using job keywords: {job_keywords}")
        
        available_keywords = [kw for kw in job_keywords if kw not in used_keywords]
        prompt = f"""
        You are an expert resume writer helping a candidate tailor their resume to a specific job.
        Rephrase the following project description to align with the target job description keywords.
        
        Target job keywords: {', '.join(available_keywords)}
        
        Original project description: {description}
        
        Your task:
        1. Incorporate at least 2-3 job keywords naturally
        2. Emphasize relevant technical skills and achievements
        3. Highlight problem-solving abilities and results
        4. Use action verbs and quantifiable metrics
        5. Maintain professional resume language
        6. Keep approximately the same length as the original
        
        Return ONLY the rephrased version with no explanations, quotes, or additional text.
        """
        
        try:
            rephrased_description = rephrase_text(prompt)
            print(f"Original: {description}\nRephrased: {rephrased_description}\n")
            
            rephrased_project = project.copy()
            rephrased_project['description'] = rephrased_description
            rephrased_projects.append(rephrased_project)
            
            # Track used keywords
            for kw in available_keywords:
                if kw in rephrased_description:
                    used_keywords.add(kw)
        except Exception as e:
            print(f"Error rephrasing project {title}: {str(e)}")
            rephrased_projects.append(project)
    
    return rephrased_projects

def enhance_resume_content(resume_data: Dict[str, Any], job_keywords: List[str]) -> Dict[str, Any]:
    """
    Enhance resume content by aligning it with job description keywords.
    
    Args:
        resume_data: The resume data to enhance
        job_keywords: The list of extracted job description keywords
        
    Returns:
        Enhanced resume data
    """
    # Ensure the skills section is a list
    if "skills" not in resume_data or not isinstance(resume_data["skills"], list):
        resume_data["skills"] = []

    existing_skills = set(s.lower() for s in resume_data["skills"])
    
    # Add unique keywords to skills section
    for skill in job_keywords:
        if skill.lower() not in existing_skills and not any(
            skill.lower() in existing.lower() or existing.lower() in skill.lower()
            for existing in resume_data["skills"]
        ):
            resume_data["skills"].append(skill)
            existing_skills.add(skill.lower())
    
    logger.info(f"Updated skills section with unique keywords. Total skills: {len(resume_data.get('skills', []))}")
    
    # Rephrase work experience and project descriptions
    if "work_experience" in resume_data:
        resume_data["work_experience"] = rephrase_work_experience(resume_data["work_experience"], job_keywords)
    
    if "projects" in resume_data:
        resume_data["projects"] = rephrase_projects(resume_data["projects"], job_keywords)
    
    return resume_data

# For testing purposes
if __name__ == "__main__":
    # Example usage with sample data
    sample_resume = {
        "experience": [
            {
                "company": "Example Corp",
                "position": "Software Engineer",
                "responsibilities": [
                    "Developed backend APIs using Python",
                    "Optimized database queries"
                ]
            }
        ],
        "projects": [
            {
                "title": "Sample Project",
                "description": "Built a machine learning model for prediction"
            }
        ],
        "extracted_keywords": {
            "technical_skills": ["Python", "API", "optimization", "SQL"],
            "soft_skills": ["communication", "teamwork"],
            "cloud_technologies": ["AWS", "Azure"],
            "programming_knowledge": ["Java", "C++"]
        }
    }
    
    enhanced = enhance_resume_content(sample_resume, sample_resume['extracted_keywords'])
    print(json.dumps(enhanced, indent=2))
