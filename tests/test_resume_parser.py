import unittest
from resume_bot.bot.resume_parser import parse_resume

class TestResumeParser(unittest.TestCase):

    def test_parse_valid_resume(self):
        # Test with a valid resume file
        resume_path = 'tests/test_files/valid_resume.pdf'
        parsed_data = parse_resume(resume_path)
        self.assertIn('name', parsed_data)
        self.assertIn('skills', parsed_data)
        self.assertIn('experience', parsed_data)
        self.assertIn('education', parsed_data)

    def test_parse_invalid_resume(self):
        # Test with an invalid resume file
        resume_path = 'tests/test_files/invalid_resume.pdf'
        parsed_data = parse_resume(resume_path)
        self.assertIsNone(parsed_data)

    def test_parse_empty_resume(self):
        # Test with an empty resume file
        resume_path = 'tests/test_files/empty_resume.pdf'
        parsed_data = parse_resume(resume_path)
        self.assertEqual(parsed_data, {})

if __name__ == '__main__':
    unittest.main()