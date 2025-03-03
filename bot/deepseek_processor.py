import json
import logging
import os
import requests
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QWENProcessor:
    """Class for processing resume text using QWEN API"""
    
    def __init__(self):
        self.api_url = "http://127.0.0.1:1234/v1/chat/completions"  # Updated to local server address
    
    def convert_to_json(self, resume_text: str) -> Optional[Dict[str, Any]]:
        """Convert resume text to structured JSON using QWEN"""
        if not resume_text or resume_text.strip() == "":
            logger.error("Empty resume text provided.")
            return None
        
        try:
            # Create prompt for QWEN
            prompt = self._create_conversion_prompt(resume_text)
            
            # Make API request
            headers = {
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "qwen2.5-7b-instruct-1m",  # Updated model identifier
                "messages": [
                    {"role": "system", "content": "You are an expert resume parser. Convert the resume text to structured JSON format."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1  # Low temperature for more deterministic responses
            }
            
            logger.info("Sending request to QWEN API")
            response = requests.post(self.api_url, headers=headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                
                # Extract JSON from the response
                try:
                    # The model should return a JSON string, but we'll handle the case where it's embedded
                    json_str = self._extract_json_from_text(content)
                    parsed_data = json.loads(json_str)
                    return parsed_data
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON from API response: {e}")
                    return None
            else:
                logger.error(f"API request failed with status code {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing resume with QWEN: {e}")
            return None
    
    def _create_conversion_prompt(self, resume_text: str) -> str:
        """Create a prompt for the QWEN API to convert resume text to JSON"""
        return f"""
        Convert the following resume text into a structured JSON format.
        Extract key information including:
        - Personal details (name, email, phone, location)
        - Education history (institutions, degrees, dates, GPA)
        - Work experience (companies, positions, dates, responsibilities)
        - Skills (technical skills, soft skills, languages)
        - Projects or publications
        - Certifications and awards

        Return the result as valid, properly formatted JSON only.

        RESUME TEXT:
        {resume_text}
        """
    
    def _extract_json_from_text(self, text: str) -> str:
        """Extract JSON string from text that might contain other content"""
        # Try to find JSON between triple backticks
        import re
        json_pattern = r"```(?:json)?(.*?)```"
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # If no backticks, try to find patterns that look like JSON objects
        if text.strip().startswith("{") and text.strip().endswith("}"):
            return text.strip()
            
        # If all else fails, return the text as is
        return text
