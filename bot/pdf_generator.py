import os
import subprocess
import logging

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
    \setlength{\textwidth}{1.2in}
    \setlength{\topmargin}{-0.7in}
    \setlength{\textheight}{1.4in}
    \raggedbottom
    \raggedright
    \begin{document}
    \section*{Name}
    {{ name }}
    \section*{Summary}
    {{ summary }}
    \section*{Skills}
    \begin{itemize}
    {% if skills %}
    {% for skill in skills %}
    \item {{ skill }}
    {% endfor %}
    {% else %}
    \item No skills listed
    {% endif %}
    \end{itemize}
    \section*{Experience}
    \begin{itemize}
    {% if experience %}
    {% for exp in experience %}
    \item {{ exp.designation }} at {{ exp.company }} ({{ exp.start_date }} - {{ exp.end_date }}): {{ exp.description }}
    {% endfor %}
    {% else %}
    \item No experience listed
    {% endif %}
    \end{itemize}
    \section*{Education}
    \begin{itemize}
    {% if education %}
    {% for edu in education %}
    \item {{ edu.degree }} in {{ edu.major }} from {{ edu.institution }} ({{ edu.year_of_passing }})
    {% endfor %}
    {% else %}
    \item No education listed
    {% endif %}
    \end{itemize}
    \section*{Projects}
    \begin{itemize}
    {% if projects %}
    {% for proj in projects %}
    \item {{ proj.title }}: {{ proj.details }}
    {% endfor %}
    {% else %}
    \item No projects listed
    {% endif %}
    \end{itemize}
    \section*{Certifications}
    \begin{itemize}
    {% if certifications %}
    {% for cert in certifications %}
    \item {{ cert }}
    {% endfor %}
    {% else %}
    \item No certifications listed
    {% endif %}
    \end{itemize}
    \end{document}
    """
    return latex_template.replace("{{ name }}", resume_data.get('name', 'Unknown')) \
                         .replace("{{ summary }}", resume_data.get('summary', '')) \
                         .replace("{% if skills %}", "{" + " ".join(resume_data.get('skills', [])) + "}") \
                         .replace("{% if experience %}", "{" + " ".join(resume_data.get('experience', [])) + "}") \
                         .replace("{% if education %}", "{" + " ".join(resume_data.get('education', [])) + "}") \
                         .replace("{% if projects %}", "{" + " ".join(resume_data.get('projects', [])) + "}") \
                         .replace("{% if certifications %}", "{" + " ".join(resume_data.get('certifications', [])) + "}")

def save_as_pdf(latex_content, output_path):
    """Save the LaTeX content as a PDF file."""
    try:
        with open("resume.tex", "w") as f:
            f.write(latex_content)
        subprocess.run(["pdflatex", "resume.tex"], check=True)
        os.rename("resume.pdf", output_path)
        os.remove("resume.tex")
        os.remove("resume.log")
        os.remove("resume.aux")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running pdflatex: {e}")
        raise

def generate_resume_pdf(resume_data, output_path):
    """Generate a PDF resume from the provided resume data."""
    latex_content = generate_latex_content(resume_data)
    save_as_pdf(latex_content, output_path)