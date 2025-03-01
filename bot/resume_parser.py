import logging
import re
from pdfminer.high_level import extract_text

logger = logging.getLogger(__name__)

def parse_resume(resume_path):
    try:
        text = extract_text(resume_path)
        if not text:
            raise ValueError("No text extracted from the resume")
        logger.info(f"Extracted text from resume: {text[:500]}...")  # Log first 500 characters
        return {"text": text}
    except Exception as e:
        logger.error(f"Error extracting text from resume: {e}")
        return {}

def clean_text(text):
    cleaned = re.sub(r'[^\x20-\x7E\n]', '', text)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

def parse_extracted_text(extracted_text):
    extracted_text = clean_text(extracted_text)
    headers = {
        "education": ["education"],
        "skills": ["skills"],
        "experience": ["experience"],
        "projects": ["projects"],
        "summary": ["summary"],
        "achievements": ["achievements"],
        "certifications": ["certifications"]
    }
    current_section = None
    data = {key: [] for key in headers}
    data["name"] = "Unknown"
    
    lines = extracted_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        lower_line = line.lower()
        header_found = False
        for section, keywords in headers.items():
            for keyword in keywords:
                if re.match(rf"^{keyword}\b", lower_line):
                    current_section = section
                    header_found = True
                    if section == "summary" and data["name"] == "Unknown":
                        data["name"] = line
                    break
            if header_found:
                break
        if current_section:
            data[current_section].append(line)
        else:
            if data["name"] == "Unknown":
                data["name"] = line
            else:
                data.setdefault("summary", []).append(line)
    return data