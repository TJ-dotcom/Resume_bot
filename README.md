# Resume Tailoring Bot

This project is a Telegram bot designed to help users tailor their resumes based on job descriptions. The bot interacts with users to gather job information and resume files, processes the data, and generates a tailored resume in PDF format.

## Project Structure

```
resume_bot
├── bot
│   ├── __init__.py
│   ├── handlers.py          # Handles Telegram bot interactions
│   ├── resume_parser.py     # Parses resume data
│   ├── t5_model.py          # Manages the T5 model for content generation
│   └── pdf_generator.py      # Generates PDF files from LaTeX templates
├── tests
│   ├── __init__.py
│   ├── test_handlers.py      # Unit tests for handlers.py
│   ├── test_resume_parser.py  # Unit tests for resume_parser.py
│   ├── test_t5_model.py      # Unit tests for t5_model.py
│   └── test_pdf_generator.py  # Unit tests for pdf_generator.py
├── bot_v1.py                # Main script to run the bot
├── requirements.txt          # Project dependencies
└── README.md                 # Project documentation
```

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