import json
from keyword_extraction import align_resume_with_job

def test_resume_alignment():
    """Test aligning a resume with a job description."""
    
    # Sample resume data
    resume_data = {
        "experience": [
            {
                "company": "Copani",
                "position": "AI application developer",
                "dates": "01/2025 – present",
                "location": "Buffalo, USA",
                "responsibilities": [
                    "Designed and implemented advanced transformer-based models for text-to-text processing.",
                    "Integrated natural language understanding (NLU) and natural language generation (NLG) capabilities into the system.",
                    "Developed AI-driven chatbots and virtual assistants capable of understanding complex technical inquiries."
                ]
            },
            {
                "company": "Cognizant",
                "position": "Software Engineer Trainee (Programmer Analyst)",
                "dates": "11/2022 – 06/2023",
                "location": "Chennai, India",
                "client": "Country Financial",
                "responsibilities": [
                    "Optimized data pipelines by developing and implementing SQL queries and stored procedures.",
                    "Resolved real-time database issues under pressure, reducing downtime by 15%.",
                    "Enhanced operational efficiency by streamlining payment reversal processes and billing workflows.",
                    "Demonstrated adaptability and problem-solving skills during early-stage project implementation."
                ]
            }
        ],
        "projects": [
            {
                "title": "Property Price Forecast",
                "dates": "05/2024",
                "description": "Hand-picked a dataset with unique features for predicting house prices. Performed EDA, PCA, and preprocessing to clean and transform the data. Implemented machine learning algorithms (Linear Regression, Random Forest) to achieve an accuracy of 87%. Deployed the model using Docker."
            },
            {
                "title": "Customer Segmentation",
                "dates": "09/2024 – 11/2024",
                "description": "Designed a scalable database solution using PostgreSQL, enhancing data retrieval speed by 30%. Integrated Power BI for reporting and analytics."
            },
            {
                "title": "Optimizing Library Management",
                "dates": "10/2024 – 11/2024",
                "description": "Developed a scalable database solution using PostgreSQL to enhance library management. Replaced Excel with advanced database features like referential integrity, concurrent access, and security measures. Integrated reporting and analytics capabilities using Power BI."
            },
            {
                "title": "Wireless Sensor Networks with Fuzzy Ant Colony Optimization",
                "dates": "03/2022 – 06/2022",
                "description": "Analyzed network traffic, sensor node power, and distance to determine optimal data routing strategies. Implemented ant colony optimization and fuzzy logic, improving energy efficiency by 20%. Designed a solution using Graph Neural Networks (GNNs) to optimize energy savings in wireless sensor networks."
            }
        ]
    }
    
    # Sample job description
    job_description = """
    Data Scientist
    
    We are looking for a Data Scientist to join our growing team. The ideal candidate will have a strong background in machine learning, statistical analysis, and data visualization.
    
    Requirements:
    - Master's degree or Ph.D. in Computer Science, Statistics, or a related field
    - 3+ years of experience with Python and data science libraries (pandas, NumPy, scikit-learn)
    - Experience with SQL and database management
    - Proficiency in developing machine learning models and algorithms
    - Experience with visualization tools like Tableau or Power BI
    - Strong communication skills and ability to present technical findings to non-technical stakeholders
    
    Responsibilities:
    - Develop predictive models and machine learning algorithms to solve business problems
    - Perform data cleaning, preprocessing, and feature engineering
    - Collaborate with cross-functional teams to understand business needs
    - Present findings and recommendations to stakeholders
    - Stay current with the latest developments in data science and machine learning
    """
    
    # Align resume with job description
    enhanced_resume = align_resume_with_job(resume_data, job_description)
    
    # Save results
    with open("original_resume.json", "w") as f:
        json.dump(resume_data, f, indent=2)
        
    with open("enhanced_resume.json", "w") as f:
        json.dump(enhanced_resume, f, indent=2)
    
    print("Resume has been aligned with the job description.")
    print("Check 'enhanced_resume.json' for the result.")
    
    # Print a sample comparison
    if enhanced_resume.get("experience") and resume_data.get("experience"):
        print("\nSAMPLE COMPARISON - WORK EXPERIENCE:")
        print("\nORIGINAL:")
        print(resume_data["experience"][0]["responsibilities"][0])
        print("\nENHANCED:")
        print(enhanced_resume["experience"][0]["responsibilities"][0])
        
        print("\nSAMPLE COMPARISON - PROJECT:")
        print("\nORIGINAL:")
        print(resume_data["projects"][0]["description"])
        print("\nENHANCED:")
        print(enhanced_resume["projects"][0]["description"])

if __name__ == "__main__":
    test_resume_alignment()
