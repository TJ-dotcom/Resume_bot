import os
import unittest
from resume_bot.bot.pdf_generator import save_as_pdf

class TestPDFGenerator(unittest.TestCase):
    def setUp(self):
        self.latex_content = r"""
        \documentclass{article}
        \begin{document}
        Hello, World!
        \end{document}
        """
        self.output_path = "test_resume.pdf"

    def test_save_as_pdf_creates_pdf(self):
        save_as_pdf(self.latex_content, self.output_path)
        self.assertTrue(os.path.exists(self.output_path))

    def tearDown(self):
        if os.path.exists(self.output_path):
            os.remove(self.output_path)

if __name__ == '__main__':
    unittest.main()