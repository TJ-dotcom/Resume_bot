import argparse
import os
from resume_bot.main import process_resume

def main():
    """Command line interface for the resume bot."""
    parser = argparse.ArgumentParser(description="Process resumes to extract and enhance content")
    parser.add_argument("resume_path", help="Path to the resume PDF file")
    parser.add_argument("--output-dir", "-o", help="Directory to save the output files")
    parser.add_argument("--no-rephrase", action="store_true", help="Skip rephrasing step")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.resume_path):
        print(f"Error: File not found - {args.resume_path}")
        return 1
    
    if args.output_dir and not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    
    try:
        output_path = process_resume(args.resume_path, args.output_dir)
        print(f"Successfully processed resume. Output saved to: {output_path}")
        return 0
    except Exception as e:
        print(f"Error processing resume: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
