import pytest
from backend.services.resume_validator import validate_resume_against_master, extract_master_skills_set


@pytest.fixture
def sample_master_profile():
    return {
        "personal": {
            "full_name": "Jordan Smith",
            "email": "jordan@example.com",
            "phone": "+1 (555) 019-2834",
            "location": "Seattle, WA",
            "linkedin_url": "https://linkedin.com/in/jordansmith",
            "github_url": "https://github.com/jordansmith"
        },
        "education": [
            {
                "degree": "B.S. in Computer Science",
                "institution": "University of Washington",
                "graduation_year": 2024,
                "score_type": "cgpa",
                "score": 3.8
            }
        ],
        "skills": {
            "languages": ["Python", "JavaScript", "SQL"],
            "frameworks": ["Flask", "React", "FastAPI"],
            "databases": ["PostgreSQL", "MongoDB"],
            "tools": ["Git", "Docker", "Postman"],
            "other": ["REST APIs", "Agile"]
        },
        "projects": [
            {
                "title": "Cloud Analytics Dashboard",
                "description": "Full-stack dashboard for visualizing cloud resource utilization.",
                "tech_stack": ["React", "Flask", "PostgreSQL"],
                "link": "https://github.com/jordansmith/cloud-dash"
            }
        ],
        "internships": [
            {
                "company": "TechCorp",
                "role": "Software Engineering Intern",
                "start_date": "Jun 2023",
                "end_date": "Aug 2023",
                "description": "Assisted backend team with RESTful APIs."
            }
        ],
        "certifications": [
            {
                "name": "AWS Certified Cloud Practitioner",
                "issuer": "Amazon Web Services",
                "year": 2023
            }
        ],
        "achievements": ["Hackathon 1st Place 2023"],
        "work_experience": [],
        "profile_status": "approved"
    }


def test_extract_master_skills_set(sample_master_profile):
    skills_map = extract_master_skills_set(sample_master_profile)
    assert "python" in skills_map
    assert skills_map["python"] == "Python"
    assert "react" in skills_map
    assert "postgresql" in skills_map
    assert "docker" in skills_map
    assert "kubernetes" not in skills_map


def test_validator_strips_unverified_skills(sample_master_profile):
    resume_content = {
        "skills": [
            {
                "category": "Languages & Frameworks",
                # Python, React are valid. Rust and Spring Boot are hallucinated/invented!
                "items": ["Python", "Rust", "React", "Spring Boot"]
            }
        ]
    }

    validated, warnings = validate_resume_against_master(resume_content, sample_master_profile)

    cat_items = validated["skills"][0]["items"]
    assert "Python" in cat_items
    assert "React" in cat_items
    assert "Rust" not in cat_items
    assert "Spring Boot" not in cat_items
    assert any("Rust" in w for w in warnings)
    assert any("Spring Boot" in w for w in warnings)


def test_validator_enforces_truthful_personal_and_education(sample_master_profile):
    resume_content = {
        "personal": {
            # Invented name and contact
            "full_name": "Dr. Master Hacker",
            "email": "hacker@evil.com",
            "phone": "000-000-0000"
        },
        "education": [
            # Invented Ph.D. degree
            {
                "degree": "Ph.D. in Artificial Intelligence",
                "institution": "MIT",
                "graduation_year": 2020
            }
        ]
    }

    validated, _ = validate_resume_against_master(resume_content, sample_master_profile)

    # Truthfulness guarantee: personal details and education reset to master profile facts
    assert validated["personal"]["full_name"] == "Jordan Smith"
    assert validated["personal"]["email"] == "jordan@example.com"
    assert validated["education"][0]["degree"] == "B.S. in Computer Science"
    assert validated["education"][0]["institution"] == "University of Washington"


def test_validator_strips_unverified_certifications(sample_master_profile):
    resume_content = {
        "certifications": [
            {"name": "AWS Certified Cloud Practitioner", "issuer": "AWS", "year": 2023},
            {"name": "Certified Ethical Hacker (CEH)", "issuer": "EC-Council", "year": 2024} # Hallucinated
        ]
    }

    validated, warnings = validate_resume_against_master(resume_content, sample_master_profile)

    cert_names = [c["name"] for c in validated["certifications"]]
    assert "AWS Certified Cloud Practitioner" in cert_names
    assert "Certified Ethical Hacker (CEH)" not in cert_names
    assert any("Certified Ethical Hacker" in w for w in warnings)

