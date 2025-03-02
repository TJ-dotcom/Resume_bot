import os
import sys
import logging
import PyPDF2
import re

logger = logging.getLogger(__name__)

def parse_resume(file_path):
    """
    Parse a resume PDF file and extract its text content.
    
    Args:
        file_path (str): Path to the PDF file
        
    Returns:
        dict: Dictionary containing the extracted text
    """
    try:
        logger.info(f"Parsing resume from {file_path}")
        
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return {"text": "", "error": "File not found"}
        
        text = ""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text()
        
        logger.info(f"Successfully parsed resume. Text length: {len(text)}")
        return {"text": text, "pages": len(reader.pages)}
    
    except Exception as e:
        logger.error(f"Error parsing PDF file: {e}", exc_info=True)
        return {"text": "", "error": str(e)}

def parse_extracted_text(text):
    """
    Parse the extracted text into different resume sections.
    
    Args:
        text (str): Extracted text from a resume
        
    Returns:
        dict: Dictionary containing different sections of the resume
    """
    try:
        if not text or not isinstance(text, str):
            logger.error(f"Invalid text input: {type(text)}")
            return {
                "name": "",
                "summary": "",
                "skills": [],
                "experience": [],
                "education": [],
                "projects": [],
                "certifications": []
            }
        
        # Basic section detection using regex patterns
        sections = {}
        
        # Extract name (usually at the top of the resume)
        name_match = re.search(r'^([\w\s]+)', text, re.MULTILINE)
        sections["name"] = name_match.group(1).strip() if name_match else ""
        
        # Extract summary/profile section
        summary_match = re.search(r'(?:SUMMARY|PROFILE|OBJECTIVE)[:]*\s*([\s\S]*?)(?:\n\n|\n[A-Z\s]+:)', text, re.IGNORECASE)
        sections["summary"] = summary_match.group(1).strip() if summary_match else ""
        
        # Extract skills section
        skills_match = re.search(r'(?:SKILLS|TECHNICAL SKILLS|EXPERTISE)[:]*\s*([\s\S]*?)(?:\n\n|\n[A-Z\s]+:)', text, re.IGNORECASE)
        if skills_match:
            skills_text = skills_match.group(1)
            skills_list = [skill.strip() for skill in re.split(r'[,•\n]', skills_text) if skill.strip()]
            sections["skills"] = skills_list
        else:
            sections["skills"] = []
        
        # Extract experience section
        experience_match = re.search(r'(?:EXPERIENCE|WORK EXPERIENCE|EMPLOYMENT)[:]*\s*([\s\S]*?)(?:\n\n|\n[A-Z\s]+:)', text, re.IGNORECASE)
        if experience_match:
            experience_text = experience_match.group(1)
            # Simplistic parsing - split by double newlines
            experience_entries = [entry.strip() for entry in re.split(r'\n\n', experience_text) if entry.strip()]
            sections["experience"] = experience_entries
        else:
            sections["experience"] = []
        
        # Extract education section
        education_match = re.search(r'(?:EDUCATION|ACADEMIC|QUALIFICATIONS)[:]*\s*([\s\S]*?)(?:\n\n|\n[A-Z\s]+:|\Z)', text, re.IGNORECASE)
        if education_match:
            education_text = education_match.group(1)
            education_entries = [entry.strip() for entry in re.split(r'\n\n', education_text) if entry.strip()]
            sections["education"] = education_entries
        else:
            sections["education"] = []
        
        # Extract projects section
        projects_match = re.search(r'(?:PROJECTS|PROJECT EXPERIENCE)[:]*\s*([\s\S]*?)(?:\n\n|\n[A-Z\s]+:|\Z)', text, re.IGNORECASE)
        if projects_match:
            projects_text = projects_match.group(1)
            projects_entries = [entry.strip() for entry in re.split(r'\n\n', projects_text) if entry.strip()]
            sections["projects"] = projects_entries
        else:
            sections["projects"] = []
        
        # Extract certifications section
        certifications_match = re.search(r'(?:CERTIFICATIONS|CERTIFICATES|ACCREDITATIONS)[:]*\s*([\s\S]*?)(?:\n\n|\n[A-Z\s]+:|\Z)', text, re.IGNORECASE)
        if certifications_match:
            certifications_text = certifications_match.group(1)
            certifications_list = [cert.strip() for cert in re.split(r'[,•\n]', certifications_text) if cert.strip()]
            sections["certifications"] = certifications_list
        else:
            sections["certifications"] = []
        
        logger.info(f"Successfully parsed resume sections: {list(sections.keys())}")
        return sections
    
    except Exception as e:
        logger.error(f"Error parsing extracted text: {e}", exc_info=True)
        return {
            "name": "",
            "summary": "",
            "skills": [],
            "experience": [],
            "education": [],
            "projects": [],
            "certifications": []
        }