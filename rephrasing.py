import json
from typing import Dict, List, Any
import os
from langchain_community.llms import Qwen
from dotenv import load_dotenv

load_dotenv()

def setup_qwen_model():
    """Initialize the Qwen model for rephrasing."""
    try:
        qwen = Qwen(
            model_name="qwen1.5-7b-chat",
            temperature=0.7,
            top_p=0.9,
            max_tokens=1024
        )
        return qwen
    except Exception as e:
        print(f"Error initializing Qwen model: {str(e)}")
        return None

def rephrase_work_experience(experience_list: List[Dict[str, Any]], job_keywords: List[str]) -> List[Dict[str, Any]]:
    """
    Rephrase work experience descriptions using Qwen while aligning with job description keywords.
    
    Args:
        experience_list: List of work experience entries
        job_keywords: List of keywords extracted from the job description
    
    Returns:
        List of rephrased work experience entries
    """
    qwen = setup_qwen_model()
    if not qwen:
        print("Failed to initialize Qwen model. Returning original experience.")
        return experience_list
    
    rephrased_experience = []
    
    for exp in experience_list:
        # Keep original company and position
        company = exp.get('company', '')
        position = exp.get('position', '')
        
        # Get responsibilities or description
        responsibilities = exp.get('responsibilities', [])
        if isinstance(responsibilities, str):
            responsibilities = [responsibilities]
        
        if not responsibilities:
            # If no responsibilities found, keep the original entry
            rephrased_experience.append(exp)
            continue
        
        print(f"Rephrasing experience for {company}, position: {position}")
        print(f"Using job keywords: {job_keywords}")
        
        rephrased_responsibilities = []
        for resp in responsibilities:
            # Create prompt for Qwen
            prompt = f"""
            You are an expert resume writer helping a candidate tailor their resume to a specific job.
            Rephrase the following job responsibility to align with the target job description keywords.
            
            Target job keywords: {', '.join(job_keywords)}
            
            Original responsibility: {resp}
            
            Your task:
            1. Incorporate at least 1-2 job keywords naturally where appropriate
            2. Emphasize relevant skills and achievements
            3. Use action verbs and quantifiable results
            4. Maintain professional resume language
            5. Keep approximately the same length as the original
            
            Return ONLY the rephrased version with no explanations, quotes, or additional text.
            """
            
            try:
                # Get rephrased responsibility
                rephrased_resp = qwen.invoke(prompt).strip()
                print(f"Original: {resp}\nRephrased: {rephrased_resp}\n")
                rephrased_responsibilities.append(rephrased_resp)
            except Exception as e:
                print(f"Error rephrasing responsibility for {company}: {str(e)}")
                rephrased_responsibilities.append(resp)  # Use original if rephrasing fails
        
        # Create the rephrased work experience entry
        rephrased_exp = exp.copy()
        rephrased_exp['responsibilities'] = rephrased_responsibilities
        rephrased_experience.append(rephrased_exp)
    
    return rephrased_experience

def rephrase_projects(projects: List[Dict[str, Any]], job_keywords: List[str]) -> List[Dict[str, Any]]:
    """
    Rephrase project descriptions using Qwen while aligning with job description keywords.
    
    Args:
        projects: List of project entries
        job_keywords: List of keywords extracted from the job description
        
    Returns:
        List of rephrased project entries
    """
    qwen = setup_qwen_model()
    if not qwen:
        print("Failed to initialize Qwen model. Returning original projects.")
        return projects
    
    rephrased_projects = []
    
    for project in projects:
        # Keep original project title
        title = project.get('title', '')
        description = project.get('description', '')
        
        if not description:
            # If no description found, keep the original entry
            rephrased_projects.append(project)
            continue
            
        print(f"Rephrasing project: {title}")
        print(f"Using job keywords: {job_keywords}")
        
        # Create prompt for Qwen
        prompt = f"""
        You are an expert resume writer helping a candidate tailor their resume to a specific job.
        Rephrase the following project description to align with the target job description keywords.
        
        Target job keywords: {', '.join(job_keywords)}
        
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
            # Get rephrased description
            rephrased_description = qwen.invoke(prompt).strip()
            print(f"Original: {description}\nRephrased: {rephrased_description}\n")
            
            # Create the rephrased project entry
            rephrased_project = project.copy()
            rephrased_project['description'] = rephrased_description
            rephrased_projects.append(rephrased_project)
        except Exception as e:
            print(f"Error rephrasing project {title}: {str(e)}")
            rephrased_projects.append(project)  # Use original if rephrasing fails
    
    return rephrased_projects

def enhance_resume_content(resume_data: dict, job_keywords: list) -> dict:
    # Dummy implementation for enhancing resume content
    resume_data['enhanced_content'] = "Enhanced content based on keywords: " + ", ".join(job_keywords)
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
        "extracted_keywords": ["Python", "API", "optimization", "SQL"]
    }
    
    enhanced = enhance_resume_content(sample_resume, sample_resume['extracted_keywords'])
    print(json.dumps(enhanced, indent=2))
