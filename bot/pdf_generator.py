import os
import sys
import subprocess
import logging

# Add current directory to path for local imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Now we can import local modules
from json_resume_converter import convert_from_json_resume

logger = logging.getLogger(__name__)

def generate_latex_content(resume_data):
    """Generate LaTeX content from the parsed resume data."""
    latex_template = r"""
    \documentclass[letterpaper,10pt]{article}
    \usepackage[empty]{fullpage}
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
    \setlength{\oddsidemargin}{-0.6in}
    \setlength{\evensidemargin}{-0.6in}
    \setlength{\textwidth}{7.5in}
    \setlength{\topmargin}{-0.7in}
    \setlength{\textheight}{9.4in}
    \raggedbottom
    \raggedright
    \begin{document}
    \section*{Name}
    {{ name }}
    \section*{Summary}
    {{ summary }}
    \section*{Skills}
    \begin{itemize}
    {{ skills }}
    \end{itemize}
    \section*{Experience}
    \begin{itemize}
    {{ experience }}
    \end{itemize>
    \section*{Education}
    \begin{itemize}
    {{ education }}
    \end{itemize>
    \section*{Projects}
    \begin{itemize}
    {{ projects }}
    \end{itemize>
    \section*{Certifications}
    \begin{itemize>
    {{ certifications }}
    \end{itemize>
    \end{document}
    """

    # Convert lists to LaTeX itemize format
    skills = "\n".join([f"\\item {skill}" for skill in resume_data.get('skills', [])])
    
    # Handle experience items which could be strings or dictionaries
    experience_items = []
    for exp in resume_data.get('experience', []):
        if isinstance(exp, dict):
            exp_text = f"\\item {exp.get('designation', '')} at {exp.get('company', '')} "
            if exp.get('start_date') and exp.get('end_date'):
                exp_text += f"({exp.get('start_date')} - {exp.get('end_date')}): "
            exp_text += exp.get('description', '')
            experience_items.append(exp_text)
        else:
            experience_items.append(f"\\item {exp}")
    experience = "\n".join(experience_items)
    
    # Handle education items which could be strings or dictionaries
    education_items = []
    for edu in resume_data.get('education', []):
        if isinstance(edu, dict):
            edu_text = f"\\item {edu.get('degree', '')} in {edu.get('major', '')} from {edu.get('institution', '')} "
            if edu.get('year_of_passing'):
                edu_text += f"({edu.get('year_of_passing')})"
            education_items.append(edu_text)
        else:
            education_items.append(f"\\item {edu}")
    education = "\n".join(education_items)
    
    # Handle projects which could be strings or dictionaries
    project_items = []
    for proj in resume_data.get('projects', []):
        if isinstance(proj, dict):
            proj_text = f"\\item {proj.get('title', '')}: {proj.get('details', '')}"
            project_items.append(proj_text)
        else:
            project_items.append(f"\\item {proj}")
    projects = "\n".join(project_items)
    
    certifications = "\n".join([f"\\item {cert}" for cert in resume_data.get('certifications', [])])

    # Replace placeholders with actual content
    latex_content = latex_template.replace("{{ name }}", resume_data.get('name', 'Unknown'))
    latex_content = latex_content.replace("{{ summary }}", resume_data.get('summary', ''))
    latex_content = latex_content.replace("{{ skills }}", skills)
    latex_content = latex_content.replace("{{ experience }}", experience)
    latex_content = latex_content.replace("{{ education }}", education)
    latex_content = latex_content.replace("{{ projects }}", projects)
    latex_content = latex_content.replace("{{ certifications }}", certifications)

    return latex_content

def save_as_pdf(latex_content, output_path):
    """Save the LaTeX content as a PDF file."""
    try:
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create temporary LaTeX file
        temp_latex_path = f"{os.path.splitext(output_path)[0]}.tex"
        with open(temp_latex_path, "w", encoding="utf-8") as f:
            f.write(latex_content)
        
        # Run pdflatex
        subprocess.run(["pdflatex", "-output-directory", os.path.dirname(output_path), temp_latex_path], 
                      check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Clean up auxiliary files
        for ext in ['.aux', '.log', '.out', '.tex']:
            aux_file = f"{os.path.splitext(output_path)[0]}{ext}"
            if os.path.exists(aux_file):
                os.remove(aux_file)
        
        return output_path
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running pdflatex: {e}")
        raise
    except Exception as e:
        logger.error(f"Error saving PDF: {e}")
        raise

def generate_resume_pdf(resume_data, output_path, force_pdf=False):
    """Generate a PDF resume from the provided resume data."""
    try:
        latex_content = generate_latex_content(resume_data)
        return save_as_pdf(latex_content, output_path)
    except Exception as e:
        logger.error(f"Error generating resume PDF: {e}")
        if force_pdf:
            # Simplified fallback for PDF generation
            return generate_simple_pdf(resume_data, output_path)
        raise

def generate_simple_pdf(resume_data, output_path):
    """Generate a simplified PDF resume from the provided resume data."""
    # Create a simpler LaTeX template for the simplified version
    latex_template = r"""
    \documentclass[letterpaper,11pt]{article}
    \usepackage[empty]{fullpage}
    \usepackage{titlesec}
    \usepackage{enumitem}
    \usepackage[hidelinks]{hyperref}
    \usepackage{fancyhdr}
    \pagestyle{fancy}
    \fancyhf{}
    \renewcommand{\headrulewidth}{0pt}
    \renewcommand{\footrulewidth}{0pt}
    \setlength{\oddsidemargin}{-0.5in}
    \setlength{\evensidemargin}{-0.5in}
    \setlength{\textwidth}{7.5in}
    \setlength{\topmargin}{-0.5in}
    \setlength{\textheight}{9.5in}
    \raggedbottom
    \raggedright
    \begin{document}
    \begin{center}
        \textbf{\Large {{ name }}}
    \end{center>

    \section*{Summary}
    {{ summary }}

    \section*{Skills}
    {{ skills }}

    \section*{Experience}
    {{ experience }}

    \section*{Education}
    {{ education }}
    \end{document}
    """

    # Format skills as comma-separated text
    skills = ", ".join(resume_data.get('skills', []))
    
    # Format experience as plain text
    experience_items = []
    for exp in resume_data.get('experience', []):
        if isinstance(exp, dict):
            exp_text = f"{exp.get('designation', '')} at {exp.get('company', '')} "
            if exp.get('start_date') and exp.get('end_date'):
                exp_text += f"({exp.get('start_date')} - {exp.get('end_date')})\n"
            exp_text += exp.get('description', '')
        else:
            exp_text = str(exp)
        experience_items.append(exp_text)
    experience = "\n\n".join(experience_items)
    
    # Format education as plain text
    education_items = []
    for edu in resume_data.get('education', []):
        if isinstance(edu, dict):
            edu_text = f"{edu.get('degree', '')} in {edu.get('major', '')} from {edu.get('institution', '')} "
            if edu.get('year_of_passing'):
                edu_text += f"({edu.get('year_of_passing')})"
        else:
            edu_text = str(edu)
        education_items.append(edu_text)
    education = "\n".join(education_items)

    # Replace placeholders with actual content
    latex_content = latex_template.replace("{{ name }}", resume_data.get('name', 'Unknown'))
    latex_content = latex_content.replace("{{ summary }}", resume_data.get('summary', ''))
    latex_content = latex_content.replace("{{ skills }}", skills)
    latex_content = latex_content.replace("{{ experience }}", experience)
    latex_content = latex_content.replace("{{ education }}", education)

    # Save as PDF using the existing function
    try:
        return save_as_pdf(latex_content, output_path)
    except Exception as e:
        logger.error(f"Error saving simple PDF: {e}")
        # Return path anyway for consistency
        return output_path

def generate_resume_pdf_from_json_schema(json_resume, output_path):
    """Generate a PDF resume from JSON Resume schema data."""
    # Convert JSON Resume schema to our internal format
    resume_data = convert_from_json_resume(json_resume)
    # Use existing function to generate PDF
    return generate_resume_pdf(resume_data, output_path)