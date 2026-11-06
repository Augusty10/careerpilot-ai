import fitz

def generate_resume_pdf(filename="Alex_Johnson_Fresher_Resume.pdf"):
    doc = fitz.open()
    page = doc.new_page()

    resume_text = """ALEX JOHNSON
alex.fresh@example.com | +1 (555) 234-5678 | San Francisco, CA
LinkedIn: https://linkedin.com/in/alex-fresher | GitHub: https://github.com/alex-fresher

OBJECTIVE
Motivated Computer Science graduate seeking an entry-level software engineering role to apply skills in modern web development, algorithms, and backend architectures.

EDUCATION
State University of Technology
Bachelor of Technology in Computer Science (2020 - 2024)
CGPA: 8.7 / 10.0

TECHNICAL SKILLS
- Programming Languages: Python, JavaScript, TypeScript, SQL
- Frameworks & Libraries: React, Node.js, Flask, Tailwind CSS
- Databases: MongoDB, PostgreSQL
- Tools & Platforms: Git, GitHub, Docker, Postman, Linux

PROJECTS
CareerPilot AI Portal (React, Flask, MongoDB)
- Built a multi-module career platform for freshers featuring JWT authentication, Bcrypt security, and interactive React dashboards.
- Deployed REST APIs with Pydantic validation and token-based protected endpoints.

Smart Job Matcher (Python, Flask)
- Engineered an NLP-based matching system that analyzes job descriptions against candidate skills to score qualification relevance.

INTERNSHIPS & EXPERIENCE
TechStart Labs | Software Engineering Intern (Jun 2023 - Aug 2023)
- Designed and integrated 8+ RESTful API endpoints using Flask and MongoDB.
- Collaborated with frontend engineers to build responsive UI components in React.

CERTIFICATIONS & ACHEIVEMENTS
- Certified Python Developer (Python Institute, 2023)
- Dean's Honor List (2023)
- 1st Place - University Hackathon 2024
"""
    page.insert_text((40, 50), resume_text, fontsize=9.5)
    doc.save(filename)
    doc.close()
    print(f"Sample PDF resume generated at {filename}")

if __name__ == "__main__":
    generate_resume_pdf()

