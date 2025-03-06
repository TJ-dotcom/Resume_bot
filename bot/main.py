import os
import logging
from pathlib import Path
from typing import Union, Dict, Any, Optional
from telegram.ext import ApplicationBuilder
from bot.handlers import start, help_command, setup_handlers, error_handler

# Import our modules
from bot.resume_parser import ResumeParser
from bot.deepseek_processor import QWENProcessor
# from bot.extraction import extract_resume_data
from bot.utils import extract_keywords_with_huggingface
from bot.rephrasing import enhance_resume_content

# Configure logging
log_file_path = Path(__file__).parent / "bot.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)
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
    
    # Extract structured data from the resume
    print("Extracting resume data...")
    resume_data = extract_resume_data(file_path)
    
    # Extract keywords from the job description
    print("Extracting keywords...")
    resume_data = extract_keywords_with_huggingface(resume_data)
    
    # Enhance content with rephrasing
    print("Enhancing resume content...")
    enhanced_resume = enhance_resume_content(resume_data)
    
    # Save results to JSON file
    output_file = output_dir / f"{file_path.stem}_enhanced.json"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(enhanced_resume, f, indent=2, ensure_ascii=False)
        logger.info(f"Enhanced resume saved to: {output_file}")
    except Exception as e:
        logger.error(f"Failed to save JSON output: {e}")
    
    return enhanced_resume

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
    # Set up logging
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Directly set the token here
    token = '8163454634:AAGwmRaAyj02ef6bxNfPnEInROivAPNeR7M'
    if not token:
        logger.error("Telegram token not set")
        return

    # Create the Application and pass it your bot's token
    application = ApplicationBuilder().token(token).build()

    # Set up handlers
    setup_handlers(application)

    # Add error handler
    application.add_error_handler(error_handler)

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
