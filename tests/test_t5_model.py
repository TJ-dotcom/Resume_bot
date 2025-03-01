import pytest
from resume_bot.bot.t5_model import T5Model

@pytest.fixture
def t5_model():
    model = T5Model()
    model.load_model()
    return model

def test_generate_section_content(t5_model):
    input_data = "generate summary: Experienced data analyst with a strong background in statistics."
    expected_output = "Experienced data analyst with a strong background in statistics."  # Adjust based on actual expected output
    output = t5_model.generate_section_content("summary", input_data)
    assert output == expected_output

def test_ensure_str_field_with_list(t5_model):
    input_data = ["Skill 1", "Skill 2", "Skill 3"]
    expected_output = "Skill 1 Skill 2 Skill 3"
    output = t5_model.ensure_str_field(input_data, "skills")
    assert output == expected_output

def test_ensure_str_field_with_dict(t5_model):
    input_data = {"key1": "value1", "key2": "value2"}
    expected_output = "key1: value1 key2: value2"
    output = t5_model.ensure_str_field(input_data, "experience")
    assert output == expected_output

def test_ensure_str_field_with_string(t5_model):
    input_data = "Just a simple string."
    expected_output = "Just a simple string."
    output = t5_model.ensure_str_field(input_data, "summary")
    assert output == expected_output

def test_generate_section_content_empty_input(t5_model):
    input_data = "generate skills: "
    expected_output = "No skills listed"  # Adjust based on actual expected output
    output = t5_model.generate_section_content("skills", input_data)
    assert output == expected_output