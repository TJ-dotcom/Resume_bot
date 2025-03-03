import os
import sys
import argparse
import json
import logging
from pathlib import Path
from typing import Union, Dict, Any, Optional

# Import our modules
from resume_parser import ResumeParser
from bot.deepseek_processor import DeepseekProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_resume_file(
    file_path: Union[str, Path], 
    output_dir: Union[str, Path] = None,
    api_key: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Process a single resume file and save the results as JSON
    
    Args:
        file_path: Path to the resume file
        output_dir: Directory to save output JSON file (defaults to same dir as input)
        api_key: Deepseek API key (optional, can use environment variable)
        
    Returns:
        Parsed resume data as dictionary, or None if parsing failed
    """
    file_path = Path(file_path)
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return None
    
    # Set default output directory if not specified
    if output_dir is None:
        output_dir = file_path.parent
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Parse the resume to extract text
    parser = ResumeParser()
    resume_text = parser.parse_resume(file_path)
    
    if resume_text is None:
        logger.error(f"Failed to parse resume: {file_path}")
        return None
    
    # Process the text with deepseek
    processor = DeepseekProcessor(api_key=api_key)
    parsed_data = processor.process_resume(resume_text)
    
    if parsed_data is None:
        logger.error(f"Failed to process resume with Deepseek: {file_path}")
        return None
    
    # Save results to JSON file
    output_file = output_dir / f"{file_path.stem}_parsed.json"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(parsed_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Parsed resume saved to: {output_file}")
    except Exception as e:
        logger.error(f"Failed to save JSON output: {e}")
    
    return parsed_data

def process_directory(
    dir_path: Union[str, Path], 
    output_dir: Union[str, Path] = None,
    api_key: Optional[str] = None,
    recursive: bool = False
) -> Dict[str, Any]:
    """
    Process all supported resume files in a directory
    
    Args:
        dir_path: Directory containing resume files
        output_dir: Directory to save output JSON files (defaults to input dir)
        api_key: Deepseek API key (optional)
        recursive: Whether to process subdirectories recursively
        
    Returns:
        Dictionary mapping file paths to parsed results
    """
    dir_path = Path(dir_path)
    if not dir_path.is_dir():
        logger.error(f"Not a directory: {dir_path}")
        return {}
    
    if output_dir is None:
        output_dir = dir_path
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get supported extensions from parser
    parser = ResumeParser()
    supported_extensions = parser.supported_extensions.keys()
    
    # Find all supported files
    results = {}
    
    # Function to process a single directory
    def process_dir(path):
        for item in path.iterdir():
            if item.is_file() and item.suffix.lower() in supported_extensions:
                result = process_resume_file(item, output_dir, api_key)
                results[str(item)] = result
            elif recursive and item.is_dir():
                process_dir(item)
    
    process_dir(dir_path)
    return results

def main():
    """Main entry point for the resume parsing tool"""
    parser = argparse.ArgumentParser(description="Resume Parser with Deepseek Integration")
    parser.add_argument("input", help="Path to resume file or directory of resume files")
    parser.add_argument("-o", "--output", help="Output directory for parsed JSON files")
    parser.add_argument("-k", "--api-key", help="Deepseek API key (can also use DEEPSEEK_API_KEY env var)")
    parser.add_argument("-r", "--recursive", action="store_true", help="Process directories recursively")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if input_path.is_file():
        process_resume_file(input_path, args.output, args.api_key)
    elif input_path.is_dir():
        process_directory(input_path, args.output, args.api_key, args.recursive)
    else:
        logger.error(f"Input path does not exist: {input_path}")
        sys.exit(1)

if __name__ == "__main__":
    main()
