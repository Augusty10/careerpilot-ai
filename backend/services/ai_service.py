import json
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import ValidationError

from backend.config import Config
from backend.models.profile import CandidateProfileSchema
from backend.models.resume import ResumeContentSchema


class AIExtractionError(Exception):
    """Exception raised when AI resume extraction fails or returns malformed data."""
    pass


EXTRACTION_SYSTEM_PROMPT = """You are an expert, meticulous resume parser for CareerPilot AI.
Extract candidate career information from the resume text into a single JSON object.

CRITICAL ANTI-HALLUCINATION RULES:
1. Extract ONLY facts, names, dates, metrics, and details that are explicitly present in the text.
2. NEVER invent, fabricate, assume, or extrapolate any degree, company, date, skill, or certification.
3. If a field or detail is not present in the text, leave it as an empty string "", null, or empty array [] as appropriate.
4. Categorize skills carefully into languages, frameworks, databases, tools, other. Do not duplicate.
5. Return ONLY a valid JSON object matching the CandidateProfile schema. Do NOT wrap in markdown fences or include commentary.

Expected JSON Structure:
{
  "personal": {
    "full_name": "...",
    "email": "...",
    "phone": "...",
    "location": "...",
    "linkedin_url": null,
    "github_url": null
  },
  "education": [
    {
      "degree": "...",
      "institution": "...",
      "graduation_year": 2024,
      "score_type": "cgpa",
      "score": 8.5
    }
  ],
  "skills": {
    "languages": ["Python", "JavaScript"],
    "frameworks": ["React", "Flask"],
    "databases": ["MongoDB"],
    "tools": ["Git", "Docker"],
    "other": ["Agile"]
  },
  "projects": [
    {
      "title": "...",
      "description": "...",
      "tech_stack": ["React", "Python"],
      "link": null
    }
  ],
  "internships": [
    {
      "company": "...",
      "role": "...",
      "start_date": "...",
      "end_date": "...",
      "description": "..."
    }
  ],
  "certifications": [
    {
      "name": "...",
      "issuer": "...",
      "year": 2023
    }
  ],
  "achievements": [],
  "work_experience": [],
  "preferred_roles": [],
  "preferred_locations": []
}
"""


RESUME_GENERATION_SYSTEM_PROMPT = """You are an expert career strategist and ATS resume specialist for CareerPilot AI.
Given a candidate's verified Master Career Profile and a target role, generate role-tailored resume content.

CRITICAL HARD TRUTHFULNESS RULES:
1. NEVER invent, fabricate, or add skills that are not present in the master profile.
2. ONLY select and reorder skills that actually exist in the master profile. Prioritize skills most relevant to the target role first.
3. NEVER alter candidate personal details (name, email, phone, links).
4. NEVER alter education details (degree, institution, graduation year, score).
5. For projects and experience: use the candidate's existing projects and experience. Highlight bullet points that demonstrate competencies aligned with the target role.
6. Write a compelling 2-3 sentence Professional Summary tailored specifically to the target role, highlighting verified master skills.
7. Return ONLY valid JSON matching the ResumeContent schema. Do NOT wrap in markdown fences or include commentary.

Expected JSON Structure:
{
  "personal": {
    "full_name": "...",
    "email": "...",
    "phone": "...",
    "location": "...",
    "linkedin_url": "...",
    "github_url": "..."
  },
  "summary": "Tailored 2-3 sentence summary...",
  "skills": [
    { "category": "Core Competencies", "items": ["Python", "Flask"] },
    { "category": "Databases & Tools", "items": ["MongoDB", "Git"] }
  ],
  "projects": [
    {
      "source_index": 0,
      "title": "...",
      "description_bullets": ["Bullet 1 with metrics", "Bullet 2 with tech"],
      "tech_stack": ["Python", "Flask"],
      "link": "..."
    }
  ],
  "internships": [
    {
      "source_index": 0,
      "company": "...",
      "role": "...",
      "start_date": "...",
      "end_date": "...",
      "description_bullets": ["Bullet 1", "Bullet 2"]
    }
  ],
  "work_experience": [],
  "education": [
    {
      "degree": "...",
      "institution": "...",
      "graduation_year": 2024,
      "score_type": "cgpa",
      "score": 8.7
    }
  ],
  "certifications": [
    { "name": "...", "issuer": "...", "year": 2023 }
  ],
  "achievements": ["..."]
}
"""


def clean_json_response(raw_text: str) -> str:
    """Strips Markdown code fences and whitespace from LLM output."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


class BaseAIProvider(ABC):
    @abstractmethod
    def extract_profile_data(self, resume_text: str) -> Dict[str, Any]:
        """Extracts structured profile data from plain text."""
        pass

    @abstractmethod
    def generate_role_tailored_resume(self, master_profile: Dict[str, Any], target_role: str) -> Dict[str, Any]:
        """Generates role-tailored structured resume content from an approved master profile."""
        pass


class MockAIProvider(BaseAIProvider):
    """
    Mock AI Provider for development and automated testing without an API key.
    Extracts recognizable keywords from resume text or returns standard fresher data.
    """

    def extract_profile_data(self, resume_text: str) -> Dict[str, Any]:
        text_lower = resume_text.lower()

        # Extract name if present or fallback
        name = "Alex Johnson"
        if "alex fresh" in text_lower:
            name = "Alex Fresh"
        elif "alex career" in text_lower:
            name = "Alex Career"

        # Detect email via regex
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", resume_text)
        email = email_match.group(0) if email_match else "alex.fresh@example.com"

        # Detect phone via regex
        phone_match = re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", resume_text)
        phone = phone_match.group(0) if phone_match else "+1 (555) 234-5678"

        # Detect degree
        degree = "B.Tech in Computer Science"
        if "master" in text_lower or "m.tech" in text_lower or "msc" in text_lower:
            degree = "M.S. in Computer Science"

        # Detect skills
        languages = []
        for lang in ["Python", "JavaScript", "TypeScript", "Java", "C++", "SQL", "Go"]:
            if lang.lower() in text_lower:
                languages.append(lang)
        if not languages:
            languages = ["Python", "JavaScript"]

        frameworks = []
        for fw in ["React", "Node.js", "Express", "Flask", "Django", "Tailwind CSS"]:
            if fw.lower() in text_lower:
                frameworks.append(fw)
        if not frameworks:
            frameworks = ["React", "Flask"]

        databases = []
        for db in ["MongoDB", "PostgreSQL", "MySQL", "Redis"]:
            if db.lower() in text_lower:
                databases.append(db)
        if not databases:
            databases = ["MongoDB"]

        tools = []
        for t in ["Git", "GitHub", "Docker", "VS Code", "Postman", "Linux"]:
            if t.lower() in text_lower:
                tools.append(t)
        if not tools:
            tools = ["Git", "Postman"]

        mock_profile = {
            "personal": {
                "full_name": name,
                "email": email,
                "phone": phone,
                "location": "San Francisco, CA",
                "linkedin_url": "https://linkedin.com/in/alex-fresher",
                "github_url": "https://github.com/alex-fresher"
            },
            "education": [
                {
                    "degree": degree,
                    "institution": "State University of Technology",
                    "graduation_year": 2024,
                    "score_type": "cgpa",
                    "score": 8.7
                }
            ],
            "skills": {
                "languages": languages,
                "frameworks": frameworks,
                "databases": databases,
                "tools": tools,
                "other": ["REST APIs", "Agile", "Data Structures"]
            },
            "projects": [
                {
                    "title": "CareerPilot AI Portal",
                    "description": "Full-stack career navigation platform with JWT auth and React Tailwind UI.",
                    "tech_stack": ["React", "Flask", "MongoDB"],
                    "link": "https://github.com/alex-fresher/careerpilot"
                },
                {
                    "title": "Smart Job Matcher",
                    "description": "Natural language processing tool matching resume competencies to job requirements.",
                    "tech_stack": ["Python", "Flask"],
                    "link": "https://github.com/alex-fresher/job-matcher"
                }
            ],
            "internships": [
                {
                    "company": "TechStart Labs",
                    "role": "Software Engineering Intern",
                    "start_date": "Jun 2023",
                    "end_date": "Aug 2023",
                    "description": "Developed RESTful APIs and assisted frontend team with React components."
                }
            ],
            "certifications": [
                {
                    "name": "Certified Python Developer",
                    "issuer": "Python Institute",
                    "year": 2023
                }
            ],
            "achievements": [
                "Dean's Honor List 2023",
                "1st Place in University Hackathon 2024"
            ],
            "work_experience": [],
            "preferred_roles": ["Frontend Engineer", "Full Stack Developer", "Software Engineer"],
            "preferred_locations": ["San Francisco, CA", "Remote"],
            "profile_status": "draft"
        }

        # Validate through schema to ensure consistency
        validated = CandidateProfileSchema(**mock_profile)
        return validated.model_dump()

    def generate_role_tailored_resume(self, master_profile: Dict[str, Any], target_role: str) -> Dict[str, Any]:
        personal = master_profile.get("personal", {})
        skills = master_profile.get("skills", {})
        all_languages = list(skills.get("languages", []))
        all_frameworks = list(skills.get("frameworks", []))
        all_databases = list(skills.get("databases", []))
        all_tools = list(skills.get("tools", []))
        all_other = list(skills.get("other", []))

        role_lower = target_role.lower()

        # Categorize and prioritize based on role
        if any(k in role_lower for k in ["python", "backend", "data", "machine", "ai"]):
            cat1_title = "Backend & Core Languages"
            cat1_items = [s for s in all_languages + all_frameworks if any(k in s.lower() for k in ["python", "flask", "django", "fastapi", "java", "sql", "c++"])]
            if not cat1_items:
                cat1_items = all_languages[:3] + all_frameworks[:2]

            cat2_title = "Databases & Infrastructure"
            cat2_items = all_databases + [t for t in all_tools if t.lower() in ["docker", "linux", "git", "postman"]]

            cat3_title = "Tools & Web Technologies"
            remaining = [s for s in all_languages + all_frameworks + all_tools + all_other if s not in cat1_items and s not in cat2_items]
            cat3_items = remaining[:6]
        elif any(k in role_lower for k in ["frontend", "ui", "react", "web", "design"]):
            cat1_title = "Frontend Technologies"
            cat1_items = [s for s in all_frameworks + all_languages if any(k in s.lower() for k in ["react", "javascript", "typescript", "tailwind", "html", "css", "vue"])]
            if not cat1_items:
                cat1_items = [s for s in all_languages if s.lower() in ["javascript", "typescript", "python"]] + all_frameworks[:3]

            cat2_title = "Backend & APIs"
            cat2_items = [s for s in all_frameworks + all_languages + all_databases if any(k in s.lower() for k in ["flask", "node", "express", "mongo", "sql"])]

            cat3_title = "Development Tools"
            remaining = [s for s in all_tools + all_other if s not in cat1_items and s not in cat2_items]
            cat3_items = remaining[:6]
        else:
            cat1_title = "Core Programming & Frameworks"
            cat1_items = (all_languages[:3] + all_frameworks[:3])
            cat2_title = "Databases & Backend"
            cat2_items = all_databases + [f for f in all_frameworks if f not in cat1_items]
            cat3_title = "Developer Tools & Methodologies"
            cat3_items = all_tools + all_other

        skills_structured = []
        if cat1_items:
            skills_structured.append({"category": cat1_title, "items": list(dict.fromkeys(cat1_items))})
        if cat2_items:
            skills_structured.append({"category": cat2_title, "items": list(dict.fromkeys(cat2_items))})
        if cat3_items:
            skills_structured.append({"category": cat3_title, "items": list(dict.fromkeys(cat3_items))})

        # Summary tailored to role
        top_skills_preview = ", ".join((cat1_items[:3] or all_languages[:2] or ["modern engineering stacks"]))
        summary = (
            f"Results-oriented aspiring {target_role} with strong hands-on proficiency in {top_skills_preview}. "
            f"Passionate about building performant, maintainable software and applying rigorous engineering practices. "
            f"Eager to contribute immediately to dynamic product teams with clean, tested code."
        )

        # Projects tailored with bullets
        projects_structured = []
        for idx, p in enumerate(master_profile.get("projects", [])):
            title = p.get("title", f"Project {idx+1}")
            tech = p.get("tech_stack", [])
            desc = p.get("description", "")
            bullets = [
                f"Architected and implemented {title} leveraging {', '.join(tech[:3]) if tech else 'modern architecture'}.",
                f"Engineered responsive user interfaces and backend logic adhering to industry standards.",
                f"Implemented automated testing, modular component design, and optimized database queries."
            ]
            if desc:
                lines = [l.strip() for l in desc.split("\n") if l.strip()]
                if lines:
                    bullets = lines[:3]
            projects_structured.append({
                "source_index": idx,
                "title": title,
                "description_bullets": bullets,
                "tech_stack": tech,
                "link": p.get("link")
            })

        # Internships
        internships_structured = []
        for idx, it in enumerate(master_profile.get("internships", [])):
            desc = it.get("description", "")
            bullets = [l.strip() for l in desc.split("\n") if l.strip()] if desc else [
                f"Collaborated with cross-functional engineering teams to ship features for {it.get('company')}.",
                f"Participated in code reviews, standups, and contributed to technical documentation."
            ]
            internships_structured.append({
                "source_index": idx,
                "company": it.get("company", ""),
                "role": it.get("role", ""),
                "start_date": it.get("start_date", ""),
                "end_date": it.get("end_date", ""),
                "description_bullets": bullets[:3]
            })

        work_structured = []
        for idx, w in enumerate(master_profile.get("work_experience", [])):
            desc = w.get("description", "")
            bullets = [l.strip() for l in desc.split("\n") if l.strip()] if desc else [
                f"Contributed to core development at {w.get('company')}."
            ]
            work_structured.append({
                "source_index": idx,
                "company": w.get("company", ""),
                "role": w.get("role", ""),
                "start_date": w.get("start_date", ""),
                "end_date": w.get("end_date", ""),
                "description_bullets": bullets[:3]
            })

        resume_content = {
            "personal": {
                "full_name": personal.get("full_name", ""),
                "email": personal.get("email", ""),
                "phone": personal.get("phone", ""),
                "location": personal.get("location", ""),
                "linkedin_url": personal.get("linkedin_url"),
                "github_url": personal.get("github_url")
            },
            "summary": summary,
            "skills": skills_structured,
            "projects": projects_structured,
            "internships": internships_structured,
            "work_experience": work_structured,
            "education": [
                {
                    "degree": e.get("degree", ""),
                    "institution": e.get("institution", ""),
                    "graduation_year": e.get("graduation_year"),
                    "score_type": e.get("score_type", "cgpa"),
                    "score": e.get("score")
                }
                for e in master_profile.get("education", [])
            ],
            "certifications": [
                {
                    "name": c.get("name", ""),
                    "issuer": c.get("issuer", ""),
                    "year": c.get("year")
                }
                for c in master_profile.get("certifications", [])
            ],
            "achievements": master_profile.get("achievements", [])
        }

        validated = ResumeContentSchema(**resume_content)
        return validated.model_dump()


class GeminiProvider(BaseAIProvider):
    """Production AI Provider using Google Gemini GenAI SDK."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model_name = model_name

    def extract_profile_data(self, resume_text: str) -> Dict[str, Any]:
        if not self.api_key:
            raise AIExtractionError("GEMINI_API_KEY is not configured.")

        from google import genai
        client = genai.Client(api_key=self.api_key)

        prompt = f"{EXTRACTION_SYSTEM_PROMPT}\n\nRESUME TEXT TO EXTRACT:\n{resume_text}"

        def call_llm(user_prompt: str) -> str:
            response = client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
            )
            return response.text

        # Attempt 1
        raw_text = call_llm(prompt)
        cleaned = clean_json_response(raw_text)

        try:
            parsed = json.loads(cleaned)
            validated = CandidateProfileSchema(**parsed)
            return validated.model_dump()
        except (json.JSONDecodeError, ValidationError) as err1:
            # Retry once with self-correction prompt
            retry_prompt = (
                f"{prompt}\n\n"
                f"NOTICE: Your previous output produced the following error: {err1}.\n"
                f"Please correct the error and output ONLY the valid raw JSON object matching the schema."
            )
            try:
                retry_text = call_llm(retry_prompt)
                retry_cleaned = clean_json_response(retry_text)
                retry_parsed = json.loads(retry_cleaned)
                validated = CandidateProfileSchema(**retry_parsed)
                return validated.model_dump()
            except Exception as err2:
                raise AIExtractionError(f"AI failed to generate valid profile JSON after retry: {err2}")

    def generate_role_tailored_resume(self, master_profile: Dict[str, Any], target_role: str) -> Dict[str, Any]:
        if not self.api_key:
            raise AIExtractionError("GEMINI_API_KEY is not configured.")

        from google import genai
        client = genai.Client(api_key=self.api_key)

        prompt = (
            f"{RESUME_GENERATION_SYSTEM_PROMPT}\n\n"
            f"TARGET ROLE:\n{target_role}\n\n"
            f"MASTER PROFILE DATA (SINGLE SOURCE OF TRUTH):\n{json.dumps(master_profile, default=str)}"
        )

        def call_llm(user_prompt: str) -> str:
            response = client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
            )
            return response.text

        raw_text = call_llm(prompt)
        cleaned = clean_json_response(raw_text)

        try:
            parsed = json.loads(cleaned)
            validated = ResumeContentSchema(**parsed)
            return validated.model_dump()
        except (json.JSONDecodeError, ValidationError) as err1:
            retry_prompt = (
                f"{prompt}\n\n"
                f"NOTICE: Your previous output produced the following error: {err1}.\n"
                f"Please correct the output and return ONLY the valid raw JSON object matching the ResumeContent schema."
            )
            try:
                retry_text = call_llm(retry_prompt)
                retry_cleaned = clean_json_response(retry_text)
                retry_parsed = json.loads(retry_cleaned)
                validated = ResumeContentSchema(**retry_parsed)
                return validated.model_dump()
            except Exception as err2:
                raise AIExtractionError(f"AI failed to generate valid resume JSON after retry: {err2}")


def get_ai_service() -> BaseAIProvider:
    """Factory returning the configured AI service provider."""
    if Config.AI_MOCK_MODE or not Config.GEMINI_API_KEY:
        return MockAIProvider()

    if Config.AI_PROVIDER.lower() == "gemini":
        return GeminiProvider(api_key=Config.GEMINI_API_KEY, model_name=Config.AI_MODEL)

    # Default fallback to mock
    return MockAIProvider()

