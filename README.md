# Resume Tailoring Bot

This project is a Telegram bot designed to help users tailor their resumes based on job descriptions. The bot interacts with users to gather job information and resume files, processes the data, and generates a tailored resume in PDF format.

## Project Structure

```
resume_bot
├── bot
│   ├── __init__.py
│   ├── handlers.py          # Handles Telegram bot interactions
│   ├── resume_parser.py     # Parses resume data
│   ├── deepseek_parser.py   # Parses resumes using Deepseek LLM
│   ├── deepseek_processor.py# Processes resume text using QWEN API
│   ├── json_resume_converter.py # Converts resume data to/from JSON Resume schema
│   ├── pdf_generator.py     # Generates PDF files from LaTeX templates
│   ├── rephrasing.py        # Rephrases and enhances resume content
│   ├── resume_enhancer.py   # Enhances resume content by aligning it with job descriptions
│   └── utils.py             # Utility functions for keyword extraction and API calls
├── tests
│   ├── __init__.py
│   ├── test_handlers.py      # Unit tests for handlers.py
│   ├── test_resume_parser.py  # Unit tests for resume_parser.py
│   ├── test_pdf_generator.py  # Unit tests for pdf_generator.py
├── bot_v1.py                # Main script to run the bot
├── cli.py                   # Command line interface for processing resumes
├── config.py                # Configuration settings
├── requirements.txt         # Project dependencies
└── README.md                # Project documentation
```

## Transformer Models and LLMs Used

### Transformer Models

1. **Tech Keyword Specialist**
   - **Model:** `ilsilfverskiold/tech-keywords-extractor`
   - **Purpose:** Extract hard technical skills/tools from job descriptions
   - **Implementation:** Used in `bot/utils.py` for extracting technical keywords.

2. **Contextual Phrase Model**
   - **Model:** `Voicelab/vlt5-base-keywords`
   - **Purpose:** Extract contextual phrases and implied skills
   - **Implementation:** Used in `bot/utils.py` for extracting contextual phrases.

3. **Zero-Shot Classification Model**
   - **Model:** `facebook/bart-large-mnli`
   - **Purpose:** Classify text into predefined categories
   - **Implementation:** Used in `bot/utils.py` for classification tasks.

### Large Language Models (LLMs)

1. **Deepseek LLM**
   - **Model:** `deepseek-r1-distill-qwen-7b`
   - **Purpose:** Parse resumes and convert them into structured JSON Resume schema
   - **Implementation:** Used in `bot/deepseek_parser.py` for parsing resumes.

2. **QWEN API**
   - **Model:** `qwen2.5-7b-instruct-1m`
   - **Purpose:** Generate text and convert resume text to structured JSON
   - **Implementation:** Used in `bot/deepseek_processor.py` and `bot/utils.py` for generating responses and processing resumes.

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd resume_bot
   ```

2. **Install dependencies:**
   It is recommended to use a virtual environment. You can create one using `venv` or `conda`.
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

3. **Set up your Telegram bot token:**
   Replace the placeholder in the `bot_v1.py` file with your actual Telegram bot token.

## Usage

1. **Run the bot:**
   ```bash
   python bot_v1.py
   ```

2. **Interact with the bot:**
   - Start the conversation with the `/start` command.
   - Provide the job title and description when prompted.
   - Upload your current resume in PDF format.
   - The bot will process the information and send you a tailored resume.

## Testing

To run the unit tests, ensure you have installed the required testing libraries and run:
```bash
pytest tests/
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.

# Resume Parser with Deepseek Integration

This module enhances the resume parsing capabilities by using specialized Python libraries to extract text from various document formats and leveraging Deepseek's AI to convert the extracted data into structured JSON.

## Features

- Parse resumes in multiple formats (PDF, DOCX, TXT, CSV, XLSX)
- Extract structured information using Deepseek AI
- Output results in clean JSON format
- Support for batch processing directories of resumes

## Installation

1. Install required dependencies:

```bash
pip install -r requirements.txt
```

2. Set up your Deepseek API key as an environment variable:

```bash
# For Linux/Mac
export DEEPSEEK_API_KEY=your_api_key_here

# For Windows
set DEEPSEEK_API_KEY=your_api_key_here
```

## Usage

### Process a single resume

```bash
python main.py path/to/resume.pdf
```

### Process all resumes in a directory

```bash
python main.py path/to/resumes_directory
```

### Specify output directory

```bash
python main.py path/to/resume.pdf -o path/to/output
```

### Process directories recursively

```bash
python main.py path/to/resumes_directory -r
```

### Provide API key directly

```bash
python main.py path/to/resume.pdf -k your_api_key_here
```

## Output Format

The parsed resume is saved as a JSON file with the following structure:

```json
{
  "personal_info": {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "123-456-7890",
    "location": "New York, NY"
  },
  "education": [
    {
      "institution": "University Name",
      "degree": "Bachelor of Science",
      "field": "Computer Science",
      "start_date": "2015-09",
      "end_date": "2019-05",
      "gpa": "3.8/4.0"
    }
  ],
  "experience": [
    {
      "company": "Company Name",
      "position": "Software Engineer",
      "start_date": "2019-06",
      "end_date": "Present",
      "responsibilities": [
        "Developed and maintained web applications",
        "Collaborated with cross-functional teams"
      ]
    }
  ],
  "skills": {
    "technical": ["Python", "JavaScript", "SQL"],
    "soft": ["Communication", "Leadership"],
    "languages": ["English", "Spanish"]
  },
  "projects": [
    {
      "name": "Project Name",
      "description": "Short description of project",
      "technologies": ["React", "Node.js"]
    }
  ],
  "certifications": [
    {
      "name": "AWS Certified Developer",
      "issuer": "Amazon Web Services",
      "date": "2020-03"
    }
  ]
}
```

## Notes

- The Deepseek API key must be provided either as an environment variable or through the command line argument.
- Make sure the input files are in supported formats.
- For best results, ensure resumes have clear formatting and structure.