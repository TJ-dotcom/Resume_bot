import os
import PyPDF2
import docx
import pandas as pd
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResumeParser:
    """Parser for extracting text from various resume formats"""
    
    def __init__(self):
        self.supported_extensions = {
            '.pdf': self._parse_pdf,
            '.docx': self._parse_docx,
            '.doc': self._parse_doc,
            '.txt': self._parse_txt,
            '.csv': self._parse_csv,
            '.xlsx': self._parse_excel,
        }
    
    def parse_resume(self, file_path):
        """Parse a resume file and extract text based on file extension"""
        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f"File does not exist: {file_path}")
            return None
            
        file_extension = file_path.suffix.lower()
        
        if file_extension not in self.supported_extensions:
            logger.error(f"Unsupported file type: {file_extension}")
            return None
            
        try:
            logger.info(f"Parsing {file_path}")
            text = self.supported_extensions[file_extension](file_path)
            return text
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return None
    
    def _parse_pdf(self, file_path):
        """Extract text from PDF files"""
        text = ""
        with open(file_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page_num in range(len(pdf_reader.pages)):
                text += pdf_reader.pages[page_num].extract_text() + "\n"
        return text
    
    def _parse_docx(self, file_path):
        """Extract text from DOCX files"""
        doc = docx.Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    
    def _parse_doc(self, file_path):
        """Handle older DOC files (requires conversion or external tools)"""
        # This is a placeholder - you might need to use a conversion tool
        # or a library like antiword, or convert to docx first
        logger.warning(f"DOC parsing is limited. Consider converting to DOCX: {file_path}")
        return f"DOC parsing not fully implemented for {file_path}"
    
    def _parse_txt(self, file_path):
        """Extract text from TXT files"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            text = file.read()
        return text
    
    def _parse_csv(self, file_path):
        """Extract text from CSV files"""
        df = pd.read_csv(file_path)
        return df.to_string()
    
    def _parse_excel(self, file_path):
        """Extract text from Excel files"""
        df = pd.read_excel(file_path)
        return df.to_string()
