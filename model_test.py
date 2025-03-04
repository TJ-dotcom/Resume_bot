import json
from bot.rephrasing import enhance_resume_content

def test_rephrasing():
    """Test the rephrasing module with sample resume data."""
    test_resume = {
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
        ],
        "extracted_keywords": [
            "SQL", "Python", "Machine Learning", "Deep Learning", "AI", 
            "Database", "Data Analysis", "Docker", "PostgreSQL", "Power BI", 
            "Optimization", "Graph Neural Networks", "NLU", "NLG"
        ]
    }
    
    print("Testing resume rephrasing...")
    enhanced_resume = enhance_resume_content(test_resume)
    
    # Save original and enhanced resumes to files for comparison
    with open("original_resume.json", "w") as f:
        json.dump(test_resume, f, indent=2)
        
    with open("enhanced_resume.json", "w") as f:
        json.dump(enhanced_resume, f, indent=2)
    
    print("Rephrasing complete. Check enhanced_resume.json for results.")
    
    # Print a quick comparison of first experience item before/after
    if enhanced_resume.get("experience") and test_resume.get("experience"):
        print("\nSAMPLE COMPARISON:")
        print("\nORIGINAL FIRST EXPERIENCE ITEM:")
        print(json.dumps(test_resume["experience"][0]["responsibilities"][0], indent=2))
        print("\nENHANCED FIRST EXPERIENCE ITEM:")
        print(json.dumps(enhanced_resume["experience"][0]["responsibilities"][0], indent=2))
        
        print("\nORIGINAL FIRST PROJECT:")
        print(json.dumps(test_resume["projects"][0]["description"], indent=2))
        print("\nENHANCED FIRST PROJECT:")
        print(json.dumps(enhanced_resume["projects"][0]["description"], indent=2))

if __name__ == "__main__":
    test_rephrasing()
