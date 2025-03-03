"""
Module for parsing resumes using the Deepseek LLM.
"""

import logging
import json
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Updated to use local server and specified model
DEEPSEEK_API_URL = "http://127.0.0.1:1234/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-r1-distill-qwen-7b"

class DeepseekParser:
    """Class to handle parsing resumes with Deepseek LLM."""
    
    def __init__(self, api_url=None, model=None):
        """Initialize the Deepseek parser with API endpoint and model."""
        self.api_url = api_url or DEEPSEEK_API_URL
        self.model = model or DEEPSEEK_MODEL
    
    def parse_resume_to_json_schema(self, resume_text: str) -> Dict[str, Any]:
        """
        Parse resume text into JSON Resume schema using Deepseek LLM.
        
        Args:
            resume_text (str): The text content of the resume
            
        Returns:
            dict: Resume data in JSON Resume schema format
        """
        # Define system prompt to explain the task
        system_prompt = """
        You are a resume parsing expert. Your task is to extract information from the provided resume 
        and format it according to the JSON Resume schema (https://github.com/jsonresume/resume-schema).
        
        Follow these guidelines:
        1. Extract all relevant information: contact details, summary, skills, work experience, 
           education, projects, and certifications.
        2. Format dates consistently (YYYY-MM-DD or YYYY-MM if day is unknown)
        3. For work experience, include company, position, dates, and summary of responsibilities
        4. For education, include institution, degree type, field of study, and graduation date
        5. Return ONLY valid JSON conforming to the JSON Resume schema, with no additional text
        
        The JSON Resume schema includes these main sections:
        - basics (name, email, phone, summary, etc.)
        - work (array of work experiences)
        - education (array of education details)
        - skills (array of skills)
        - projects (array of projects)
        - certificates (array of certifications)
        """
        
        # User message containing the resume to parse
        user_message = f"Please parse this resume into JSON Resume schema format:\n\n{resume_text}"
        
        try:
            # Make the API request to Deepseek
            response = self._call_deepseek_api(system_prompt, user_message)
            
            # Extract and parse the JSON from the response
            json_resume = self._extract_json_from_response(response)
            
            # Validate the JSON structure
            self._validate_json_resume(json_resume)
            
            return json_resume
        
        except Exception as e:
            logger.error(f"Error parsing resume with Deepseek: {e}")
            # Return empty schema as fallback
            return self._get_empty_schema()
    
    def _call_deepseek_api(self, system_prompt: str, user_message: str) -> Dict[str, Any]:
        """Make an API call to local Deepseek server."""
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.1,  # Lower temperature for more deterministic outputs
            "max_tokens": 2000
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to Deepseek API: {e}")
            raise
    
    def _extract_json_from_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract JSON from the Deepseek response."""
        # Adapt this based on the actual response format from Deepseek
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Extract JSON part if the response contains markdown code blocks
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.rfind("```")
            content = content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.rfind("```")
            content = content[start:end].strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Deepseek response: {e}")
            logger.debug(f"Response content: {content}")
            raise
    
    def _validate_json_resume(self, json_resume: Dict[str, Any]) -> None:
        """Perform basic validation of the JSON Resume schema."""
        required_sections = ["basics", "skills"]
        
        for section in required_sections:
            if section not in json_resume:
                logger.warning(f"Missing required section in parsed resume: {section}")
                # Add empty section rather than failing
                json_resume[section] = {} if section == "basics" else []
        
        # Ensure basics section has minimum required fields
        if "basics" in json_resume and isinstance(json_resume["basics"], dict):
            if not json_resume["basics"].get("name"):
                logger.warning("Name missing from parsed resume")
    
    def _get_empty_schema(self) -> Dict[str, Any]:
        """Return an empty JSON Resume schema."""
        return {
            "basics": {
                "name": "",
                "label": "",
                "email": "",
                "phone": "",
                "summary": "",
                "profiles": []
            },
            "work": [],
            "education": [],
            "skills": [],
            "projects": [],
            "certificates": []
        }
