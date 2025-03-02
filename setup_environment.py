
import subprocess
import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("setup")

def install_requirements():
    """Install required Python packages"""
    try:
        logger.info("Installing required Python packages...")
        
        # Install basic requirements
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        
        # Try to install specific PDF libraries separately to handle any issues
        pdf_libs = [
            "reportlab>=3.6.1", 
            "Pillow>=9.0.0", 
            "fpdf2>=2.6.0",
            "weasyprint>=53.0",
            "cairocffi>=1.2.0"
        ]
        
        for lib in pdf_libs:
            try:
                logger.info(f"Installing {lib}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
                logger.info(f"Successfully installed {lib}")
            except Exception as e:
                logger.warning(f"Could not install {lib}: {e}")
        
        logger.info("All packages installed successfully")
    except Exception as e:
        logger.error(f"Error installing requirements: {e}")
        return False
    
    return True

def create_directories():
    """Create necessary directories"""
    try:
        dirs = ["resumes", "resumes/outputs", "logs"]
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
        logger.info("Directory structure created")
    except Exception as e:
        logger.error(f"Error creating directories: {e}")
        return False
    
    return True

def check_pdf_generation():
    """Check if PDF generation tools are working"""
    try:
        import reportlab
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create a simple test PDF with ReportLab
        test_pdf_path = "test_reportlab.pdf"
        c = canvas.Canvas(test_pdf_path, pagesize=letter)
        c.drawString(100, 750, "PDF generation with ReportLab is working!")
        c.save()
        
        if os.path.exists(test_pdf_path):
            logger.info("ReportLab PDF generation is working properly")
            os.remove(test_pdf_path)
            return True
        
        logger.warning("ReportLab couldn't generate a PDF")
        return False
    except ImportError:
        logger.warning("ReportLab is not installed properly")
        return False
    except Exception as e:
        logger.error(f"Error testing PDF generation: {e}")
        return False

def main():
    """Main setup function"""
    logger.info("Starting environment setup...")
    
    success = True
    if not install_requirements():
        success = False
    
    if not create_directories():
        success = False
    
    if not check_pdf_generation():
        success = False
        logger.warning("PDF generation may not work properly. The bot will fallback to text files.")
        logger.info("To fix PDF generation, please try:")
        logger.info("1. Install Microsoft Visual C++ Build Tools")
        logger.info("2. For WeasyPrint: Install GTK3 (https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer)")
    
    if success:
        logger.info("Environment setup completed successfully!")
    else:
        logger.warning("Environment setup completed with some issues. The bot will try to work with available functionality.")
    
    input("Press Enter to continue...")

if __name__ == "__main__":
    main()
