import os
import subprocess
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

def generate_latex_content(resume_data):
    """Generate LaTeX content from the parsed resume data."""
    logger.info(f"Generating LaTeX content from data with keys: {resume_data.keys()}")
    
    latex_template = r"""
\documentclass[letterpaper,10pt]{article}
\usepackage[margin=0.75in]{geometry}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage{multicol}
\usepackage{xcolor}
\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

\begin{document}
\begin{center}
{\Large\bfseries NAME}\\
\end{center}

\section*{Summary}
NAME_PLACEHOLDER

\section*{Skills}
\begin{itemize}[leftmargin=*]
SKILLS_PLACEHOLDER
\end{itemize}

\section*{Experience}
\begin{itemize}[leftmargin=*]
EXPERIENCE_PLACEHOLDER
\end{itemize}

\section*{Education}
\begin{itemize}[leftmargin=*]
EDUCATION_PLACEHOLDER
\end{itemize}

\section*{Projects}
\begin{itemize}[leftmargin=*]
PROJECTS_PLACEHOLDER
\end{itemize}

\section*{Certifications}
\begin{itemize}[leftmargin=*]
CERTIFICATIONS_PLACEHOLDER
\end{itemize}
\end{document}
    """

    # Format name
    name = resume_data.get('name', 'Unknown')
    
    # Process skills section - expecting list of strings
    skills_items = []
    for skill in resume_data.get('skills', []):
        if isinstance(skill, str):
            skills_items.append(f"\\item {skill}")
    skills = "\n".join(skills_items)
    
    # Process experience section - handle both strings and dictionaries
    experience_items = []
    for exp in resume_data.get('experience', []):
        if isinstance(exp, dict):
            # Handle dictionary format (original expected format)
            try:
                experience_items.append(
                    f"\\item {exp.get('designation', 'Role')} at {exp.get('company', 'Company')} "
                    f"({exp.get('start_date', 'Start')} - {exp.get('end_date', 'Present')}): "
                    f"{exp.get('description', 'Description')}"
                )
            except Exception as e:
                logger.error(f"Error processing experience dictionary: {e}")
                experience_items.append(f"\\item {str(exp)}")
        elif isinstance(exp, str):
            # Handle string format (what we're actually getting)
            experience_items.append(f"\\item {exp}")
    experience = "\n".join(experience_items)
    
    # Process education section - handle both strings and dictionaries
    education_items = []
    for edu in resume_data.get('education', []):
        if isinstance(edu, dict):
            try:
                education_items.append(
                    f"\\item {edu.get('degree', 'Degree')} in {edu.get('major', 'Field')} "
                    f"from {edu.get('institution', 'School')} ({edu.get('year_of_passing', 'Year')})"
                )
            except Exception as e:
                logger.error(f"Error processing education dictionary: {e}")
                education_items.append(f"\\item {str(edu)}")
        elif isinstance(edu, str):
            education_items.append(f"\\item {edu}")
    education = "\n".join(education_items)
    
    # Process projects section - handle both strings and dictionaries
    projects_items = []
    for proj in resume_data.get('projects', []):
        if isinstance(proj, dict):
            try:
                projects_items.append(f"\\item {proj.get('title', 'Project')}: {proj.get('details', 'Description')}")
            except Exception as e:
                logger.error(f"Error processing project dictionary: {e}")
                projects_items.append(f"\\item {str(proj)}")
        elif isinstance(proj, str):
            projects_items.append(f"\\item {proj}")
    projects = "\n".join(projects_items)
    
    # Process certifications - expecting list of strings
    certifications_items = []
    for cert in resume_data.get('certifications', []):
        if isinstance(cert, str):
            certifications_items.append(f"\\item {cert}")
    certifications = "\n".join(certifications_items)
    
    # Replace placeholders with actual content
    latex_content = latex_template.replace("NAME_PLACEHOLDER", name)
    latex_content = latex_content.replace("SKILLS_PLACEHOLDER", skills)
    latex_content = latex_content.replace("EXPERIENCE_PLACEHOLDER", experience)
    latex_content = latex_content.replace("EDUCATION_PLACEHOLDER", education)
    latex_content = latex_content.replace("PROJECTS_PLACEHOLDER", projects)
    latex_content = latex_content.replace("CERTIFICATIONS_PLACEHOLDER", certifications)
    
    return latex_content

def save_as_pdf(latex_content, output_path, resume_data):
    """
    Save the LaTeX content as a PDF file using pdflatex if available,
    otherwise create a simple text file as fallback.
    
    Args:
        latex_content (str): The LaTeX content to convert
        output_path (str): Path to save the output file
        resume_data (dict): Resume data for fallback text file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = f"resume_{timestamp}"
    tex_file = f"{base_path}.tex"
    pdf_file = f"{base_path}.pdf"
    
    try:
        # Write LaTeX content to file
        with open(tex_file, "w", encoding="utf-8") as f:
            f.write(latex_content)
        
        # Try to run pdflatex
        try:
            logger.info(f"Attempting to run pdflatex on {tex_file}")
            # Run pdflatex with timeout
            process = subprocess.run(
                ["pdflatex", tex_file],
                capture_output=True,
                text=True,
                timeout=60  # Increase timeout to 60 seconds
            )
            
            if process.returncode == 0 and os.path.exists(pdf_file):
                # Success - move the file to requested output path
                os.rename(pdf_file, output_path)
                logger.info(f"Successfully created PDF at {output_path}")
            else:
                # pdflatex ran but failed
                logger.error(f"pdflatex failed: {process.stderr}")
                raise Exception("pdflatex command failed")
                
        except (subprocess.SubprocessError, Exception) as e:
            # If pdflatex fails, create a text file as fallback
            logger.warning(f"Failed to generate PDF using pdflatex: {e}. Creating text file as fallback.")
            fallback_output = f"{base_path}.txt"
            
            # Create a simple text version of the resume
            with open(fallback_output, "w", encoding="utf-8") as f:
                # Use the resume_data parameter that was passed in
                f.write("# RESUME\n\n")
                f.write(f"## {resume_data.get('name', 'Name')}\n\n")
                
                f.write("## Summary\n")
                f.write(f"{resume_data.get('summary', '')}\n\n")
                
                f.write("## Skills\n")
                for skill in resume_data.get('skills', []):
                    f.write(f"- {skill}\n")
                f.write("\n")
                
                f.write("## Experience\n")
                for exp in resume_data.get('experience', []):
                    f.write(f"- {exp}\n")
                f.write("\n")
                
                f.write("## Education\n")
                for edu in resume_data.get('education', []):
                    f.write(f"- {edu}\n")
                f.write("\n")
                
                f.write("## Projects\n")
                for proj in resume_data.get('projects', []):
                    f.write(f"- {proj}\n")
                f.write("\n")
                
                f.write("## Certifications\n")
                for cert in resume_data.get('certifications', []):
                    f.write(f"- {cert}\n")
            
            os.rename(fallback_output, output_path)
            logger.info(f"Created text file as fallback at {output_path}")
    
    except Exception as e:
        logger.error(f"Error saving PDF: {e}", exc_info=True)
        
        # Create an even simpler emergency fallback
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("# RESUME (Emergency Fallback)\n\n")
                f.write("An error occurred while generating your resume.\n")
                f.write("Please try again or contact support.\n")
            logger.info(f"Created emergency fallback file at {output_path}")
        except:
            logger.critical("Failed to create even the emergency fallback file")
            raise
    
    finally:
        # Clean up temporary files
        for ext in [".tex", ".aux", ".log"]:
            temp_file = f"{base_path}{ext}"
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    logger.warning(f"Could not remove temporary file {temp_file}: {e}")
    
    return output_path

def generate_resume_pdf(resume_data, output_path):
    """Generate a PDF resume from the provided resume data."""
    logger.info(f"Generating resume PDF with sections: {list(resume_data.keys())}")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Generate LaTeX and create PDF
        latex_content = generate_latex_content(resume_data)
        
        # Pass resume_data to save_as_pdf for fallback text file
        return save_as_pdf(latex_content, output_path, resume_data)
    except Exception as e:
        logger.error(f"Error in generate_resume_pdf: {e}", exc_info=True)
        
        # Create a simple text file if everything fails
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("# Resume (Error Recovery)\n\n")
                f.write("Skills:\n")
                for skill in resume_data.get('skills', []):
                    f.write(f"- {skill}\n")
                f.write("\nExperience:\n")
                for exp in resume_data.get('experience', []):
                    f.write(f"- {exp}\n")
            return output_path
        except:
            logger.critical("Failed even in error recovery mode")
            raise