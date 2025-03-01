import logging
from transformers import T5ForConditionalGeneration, T5Tokenizer

logger = logging.getLogger(__name__)

class T5ModelManager:
    def __init__(self, model_name='nakamoto-yama/t5-resume-generation'):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.load_model()

    def load_model(self):
        """Load the T5 model and tokenizer."""
        try:
            self.model = T5ForConditionalGeneration.from_pretrained(self.model_name)
            self.tokenizer = T5Tokenizer.from_pretrained(self.model_name)
            logger.info("T5 model and tokenizer loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading T5 model: {e}")
            raise

    def generate_section_content(self, section, content):
        """Generate content for each section using the T5 model."""
        input_text = f"generate {section}: {content}"
        input_ids = self.tokenizer.encode(input_text, return_tensors="pt")
        output_ids = self.model.generate(input_ids, max_length=512, num_beams=4, early_stopping=True)
        output_text = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        logger.info(f"Generated content for section '{section}': {output_text}")
        return output_text

def ensure_str_field(field):
    """Ensure the field is a string for the T5 model."""
    if isinstance(field, list):
        return " ".join(field)
    elif isinstance(field, dict):
        return " ".join([f"{k}: {v}" for k, v in field.items()])
    return str(field)