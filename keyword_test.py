from keyword_extraction import extract_keywords_from_job_description, normalize_keywords

def test_keyword_extraction():
    """Test the keyword extraction and normalization functionality."""
    
    # Test with duplicate/redundant skills
    test_job_description = """
    Data Analyst
    
    Requirements:
    • Technical Skills: SQL skills, R programming, Python programming, Metabase BI tool, 
      Snowflake cloud platform, Amplitude analytics tool, Data engineering, Database work, 
      Self-service tools creation
    • Soft Skills: Strong project management, Organizational skills, Ability to manage multiple priorities, 
      Meet deadlines, Attention to detail, Work with large datasets, Uncover meaningful patterns and trends, 
      Intellectual curiosity, Self-driven in unstructured environments, Communicate effectively, 
      Provide meaningful insights
    • Cloud Technologies: Snowflake cloud platform
    • Programming Knowledge: SQL skills, R programming, Python programming
    """
    
    print("Testing keyword extraction and normalization...")
    keywords = extract_keywords_from_job_description(test_job_description)
    
    print("\nExtracted keywords after normalization:")
    for i, kw in enumerate(keywords, 1):
        print(f"{i}. {kw}")
    
    print(f"\nTotal unique keywords: {len(keywords)}")
    
    # Test normalization function directly
    print("\nTesting normalization function directly:")
    test_keywords = [
        "SQL skills", 
        "Python programming",
        "R programming skills",
        "experience with Snowflake",
        "Snowflake cloud platform",
        "proficient in SQL",
        "knowledge of database work",
        "Database",
        "Metabase BI tool",
        "SQL"
    ]
    
    print("Before normalization:", test_keywords)
    normalized = normalize_keywords(test_keywords)
    print("After normalization:", normalized)
    
    # Test another example with different duplications
    print("\nTesting another job description:")
    another_job = """
    Machine Learning Engineer
    
    Requirements:
    - Expertise in ML and Machine Learning algorithms
    - Strong Python programming skills
    - Experience with TensorFlow or PyTorch
    - Knowledge of NLP and Natural Language Processing
    - Proficiency in SQL and databases
    - Experience with cloud platforms (AWS preferred)
    - Understanding of Docker containers and Kubernetes (k8s)
    """
    
    another_keywords = extract_keywords_from_job_description(another_job)
    print("Extracted keywords:")
    for i, kw in enumerate(another_keywords, 1):
        print(f"{i}. {kw}")

if __name__ == "__main__":
    test_keyword_extraction()
