import json
import argparse
from typing import Dict, Any, List
from bot.utils import extract_keywords_with_huggingface
from bot.rephrasing import enhance_resume_content

def load_json_file(file_path: str) -> Dict:
    """Load JSON data from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return {}

def save_json_file(data: Dict, file_path: str) -> bool:
    """Save JSON data to a file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving JSON file: {e}")
        return False

def enhance_resume_content(resume_data: Dict[str, Any], job_keywords: List[str]) -> Dict[str, Any]:
    """
    Enhance resume content by aligning it with job description keywords.
    
    Args:
        resume_data: The resume data to enhance
        job_keywords: The list of extracted job description keywords
        
    Returns:
        Enhanced resume data
    """
    # Add relevant keywords to skills section
    if "skills" not in resume_data:
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

def enhance_resume(resume_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
    """
    Enhance a resume by aligning it with a job description.
    
    Args:
        resume_data: The resume data to enhance
        job_description: The job description text
        
    Returns:
        Enhanced resume data
    """
    # Extract keywords from job description
    print("Extracting keywords from job description...")
    job_keywords = extract_keywords_with_huggingface(job_description)
    
    # Eliminate duplicates
    job_keywords = list(set(job_keywords))
    
    print(f"Extracted keywords: {job_keywords}")
    
    # Store job description and keywords in resume data
    resume_data['job_description'] = job_description
    resume_data['job_description_keywords'] = job_keywords
    
    # Enhance resume content
    print("Enhancing resume content...")
    enhanced_resume = enhance_resume_content(resume_data, job_keywords)
    
    return enhanced_resume

def main():
    parser = argparse.ArgumentParser(description="Enhance a resume to align with a job description")
    parser.add_argument("--resume", help="Path to resume JSON file", required=True)
    parser.add_argument("--job", help="Path to job description text file", required=True)
    parser.add_argument("--output", help="Output file path for enhanced resume", default="enhanced_resume.json")
    
    args = parser.parse_args()
    
    # Load resume data
    resume_data = load_json_file(args.resume)
    if not resume_data:
        print("Failed to load resume data.")
        return
    
    # Load job description
    try:
        with open(args.job, 'r', encoding='utf-8') as file:
            job_description = file.read()
    except Exception as e:
        print(f"Error loading job description: {e}")
        return
    
    # Enhance resume
    enhanced_resume = enhance_resume(resume_data, job_description)
    
    # Save enhanced resume
    if save_json_file(enhanced_resume, args.output):
        print(f"Enhanced resume saved to {args.output}")
    else:
        print("Failed to save enhanced resume.")

if __name__ == "__main__":
    main()
