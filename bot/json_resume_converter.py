"""
Module for converting between our internal resume format and the JSON Resume schema.
JSON Resume schema: https://github.com/jsonresume/resume-schema
"""

import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def convert_to_json_resume(resume_data):
    """
    Convert our internal resume format to JSON Resume schema.
    
    Args:
        resume_data (dict): Resume data in our internal format
        
    Returns:
        dict: Resume data formatted according to JSON Resume schema
    """
    json_resume = {
        "basics": {
            "name": resume_data.get("name", ""),
            "summary": resume_data.get("summary", ""),
            "email": resume_data.get("email", ""),
            "phone": resume_data.get("phone", ""),
            "profiles": []
        },
        "skills": [{"name": skill, "level": ""} for skill in resume_data.get("skills", [])],
        "work": [],
        "education": [],
        "projects": [],
        "certificates": []
    }
    
    # Convert experience entries
    for exp in resume_data.get("experience", []):
        work_entry = {
            "company": exp.get("company", ""),
            "position": exp.get("designation", ""),
            "startDate": exp.get("start_date", ""),
            "endDate": exp.get("end_date", "") or "Present",
            "summary": exp.get("description", "")
        }
        json_resume["work"].append(work_entry)
    
    # Convert education entries
    for edu in resume_data.get("education", []):
        education_entry = {
            "institution": edu.get("institution", ""),
            "area": edu.get("major", ""),
            "studyType": edu.get("degree", ""),
            "endDate": edu.get("year_of_passing", ""),
        }
        json_resume["education"].append(education_entry)
    
    # Convert project entries
    for proj in resume_data.get("projects", []):
        project_entry = {
            "name": proj.get("title", ""),
            "description": proj.get("details", ""),
        }
        json_resume["projects"].append(project_entry)
    
    # Convert certifications
    for cert in resume_data.get("certifications", []):
        cert_entry = {
            "name": cert,
            "date": "",
            "issuer": ""
        }
        json_resume["certificates"].append(cert_entry)
    
    return json_resume

def convert_from_json_resume(json_resume):
    """
    Convert from JSON Resume schema to our internal resume format.
    
    Args:
        json_resume (dict): Resume data in JSON Resume schema
        
    Returns:
        dict: Resume data in our internal format
    """
    resume_data = {
        "name": json_resume.get("basics", {}).get("name", ""),
        "summary": json_resume.get("basics", {}).get("summary", ""),
        "email": json_resume.get("basics", {}).get("email", ""),
        "phone": json_resume.get("basics", {}).get("phone", ""),
        "skills": [skill.get("name") for skill in json_resume.get("skills", [])],
        "experience": [],
        "education": [],
        "projects": [],
        "certifications": []
    }
    
    # Convert work experience
    for work in json_resume.get("work", []):
        exp_entry = {
            "company": work.get("company", ""),
            "designation": work.get("position", ""),
            "start_date": work.get("startDate", ""),
            "end_date": work.get("endDate", "") if work.get("endDate") != "Present" else "",
            "description": work.get("summary", "")
        }
        resume_data["experience"].append(exp_entry)
    
    # Convert education
    for edu in json_resume.get("education", []):
        edu_entry = {
            "institution": edu.get("institution", ""),
            "major": edu.get("area", ""),
            "degree": edu.get("studyType", ""),
            "year_of_passing": edu.get("endDate", "")
        }
        resume_data["education"].append(edu_entry)
    
    # Convert projects
    for proj in json_resume.get("projects", []):
        proj_entry = {
            "title": proj.get("name", ""),
            "details": proj.get("description", "")
        }
        resume_data["projects"].append(proj_entry)
    
    # Convert certificates
    resume_data["certifications"] = [cert.get("name", "") for cert in json_resume.get("certificates", [])]
    
    return resume_data

def parse_resume_with_deepseek(resume_text):
    """
    Parse resume text using Deepseek and convert to JSON Resume schema.
    
    Args:
        resume_text (str): The text content of the resume
        
    Returns:
        dict: Resume data in JSON Resume schema format
    """
    # This is a placeholder for the actual implementation using Deepseek
    # In a real implementation, we would make an API call to Deepseek here
    
    # For now, we'll return a skeleton JSON Resume schema
    return {
        "basics": {
            "name": "",
            "summary": "",
            "email": "",
            "phone": "",
            "profiles": []
        },
        "skills": [],
        "work": [],
        "education": [],
        "projects": [],
        "certificates": []
    }

def validate_json_resume(json_resume):
    """
    Validate a resume against the JSON Resume schema.
    
    Args:
        json_resume (dict): Resume data in JSON Resume schema format
        
    Returns:
        bool: True if valid, False otherwise
    """
    required_sections = ["basics", "skills", "work", "education"]
    
    # Basic validation - check if required sections exist
    for section in required_sections:
        if section not in json_resume:
            logger.warning(f"Missing required section: {section}")
            return False
    
    # Check if basics has required fields
    if not json_resume["basics"].get("name"):
        logger.warning("Missing name in basics section")
        return False
    
    return True
