import re
from typing import Dict, List, Optional, Tuple, Set


# Curated alias and synonym dictionary (canonical lower-case target)
ALIAS_DICTIONARY: Dict[str, str] = {
    # JavaScript / TypeScript / Node
    "reactjs": "react",
    "react.js": "react",
    "react js": "react",
    "react": "react",
    "nodejs": "node.js",
    "node.js": "node.js",
    "node js": "node.js",
    "node": "node.js",
    "javascript": "javascript",
    "js": "javascript",
    "typescript": "typescript",
    "ts": "typescript",
    "expressjs": "express.js",
    "express.js": "express.js",
    "express": "express.js",
    "nextjs": "next.js",
    "next.js": "next.js",
    "vuejs": "vue",
    "vue.js": "vue",
    "vue": "vue",
    "angularjs": "angular",
    "angular.js": "angular",
    "angular": "angular",

    # Python
    "python": "python",
    "python3": "python",
    "py": "python",
    "django": "django",
    "flask": "flask",
    "fastapi": "fastapi",

    # Databases
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "postgre sql": "postgresql",
    "mongodb": "mongodb",
    "mongo": "mongodb",
    "mongo db": "mongodb",
    "mysql": "mysql",
    "my sql": "mysql",
    "sqlite": "sqlite",
    "redis": "redis",
    "sql": "sql",
    "rdbms": "sql",
    "relational database": "sql",

    # Cloud & DevOps
    "aws": "aws",
    "amazon web services": "aws",
    "azure": "azure",
    "microsoft azure": "azure",
    "gcp": "gcp",
    "google cloud platform": "gcp",
    "google cloud": "gcp",
    "docker": "docker",
    "containerization": "docker",
    "kubernetes": "kubernetes",
    "k8s": "kubernetes",
    "git": "git",
    "github": "git",
    "gitlab": "git",
    "version control": "git",
    "ci/cd": "ci/cd",
    "cicd": "ci/cd",
    "jenkins": "jenkins",

    # Web & APIs
    "rest": "rest apis",
    "rest api": "rest apis",
    "rest apis": "rest apis",
    "restful": "rest apis",
    "restful api": "rest apis",
    "restful apis": "rest apis",
    "graphql": "graphql",
    "html": "html",
    "html5": "html",
    "css": "css",
    "css3": "css",
    "tailwind": "tailwind css",
    "tailwindcss": "tailwind css",
    "tailwind css": "tailwind css",
    "bootstrap": "bootstrap",

    # Java / C# / C++
    "core java": "java",
    "java": "java",
    "c++": "c++",
    "cpp": "c++",
    "c#": "c#",
    "csharp": "c#",
    ".net": ".net",
    "dotnet": ".net",
    "asp.net": "asp.net",
    "golang": "go",
    "go lang": "go",
    "go": "go",

    # Testing & QA
    "selenium": "selenium",
    "playwright": "playwright",
    "cypress": "cypress",
    "junit": "junit",
    "pytest": "pytest",
    "manual testing": "manual testing",
    "automation testing": "automation testing",

    # Data Science & ML
    "pandas": "pandas",
    "numpy": "numpy",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "tensorflow": "tensorflow",
    "pytorch": "pytorch",
    "tableau": "tableau",
    "powerbi": "power bi",
    "power bi": "power bi",
    "excel": "excel",
    "advanced excel": "excel"
}


# Curated related skills dictionary for deterministic fallback / mock semantic matching
# Maps (job_skill, candidate_skill) -> explanation of relationship
RELATED_SKILLS_MAP: Dict[Tuple[str, str], str] = {
    ("django", "flask"): "Alternative Python web framework with similar MVC/MTV concepts",
    ("flask", "django"): "Alternative Python web framework",
    ("django", "fastapi"): "Alternative Python backend framework",
    ("fastapi", "flask"): "Related lightweight Python API framework",
    ("fastapi", "django"): "Related Python web framework",
    ("flask", "fastapi"): "Related Python microframework",

    ("react", "vue"): "Alternative modern frontend component framework",
    ("vue", "react"): "Alternative component-based frontend framework",
    ("react", "angular"): "Alternative frontend component architecture",
    ("angular", "react"): "Alternative frontend framework",
    ("vue", "angular"): "Alternative frontend component framework",

    ("postgresql", "mysql"): "Related relational SQL database with similar SQL dialect",
    ("mysql", "postgresql"): "Related relational SQL database",
    ("mongodb", "couchdb"): "Related NoSQL document database",
    ("redis", "memcached"): "Related in-memory cache/store",

    ("selenium", "playwright"): "Alternative modern test automation framework",
    ("playwright", "selenium"): "Alternative browser automation tool",
    ("cypress", "selenium"): "Alternative end-to-end testing tool",
    ("selenium", "cypress"): "Alternative web automation tool",

    ("express.js", "nestjs"): "Related Node.js backend framework",
    ("nestjs", "express.js"): "Related Node.js server framework",

    ("pytorch", "tensorflow"): "Alternative deep learning framework with tensor computation",
    ("tensorflow", "pytorch"): "Alternative machine learning framework",

    ("tailwind css", "bootstrap"): "Alternative popular utility/component CSS framework",
    ("bootstrap", "tailwind css"): "Alternative CSS layout framework",

    ("pandas", "polars"): "Alternative DataFrame library for data manipulation"
}


def normalize_skill(skill_str: str) -> str:
    """
    Normalizes a skill string to its canonical representation:
    - Strips whitespace and lowercases.
    - Preserves important syntax characters like '+', '#', '.', and '-'.
    - Performs alias lookup in ALIAS_DICTIONARY.
    """
    if not skill_str:
        return ""

    raw = skill_str.strip().lower()

    # Remove enclosing quotes, brackets, or bullets
    raw = re.sub(r"^[\s\"\'\[\(\*\-\•]+|[\s\"\'\]\)\*\-]+$", "", raw).strip()

    # Direct alias lookup
    if raw in ALIAS_DICTIONARY:
        return ALIAS_DICTIONARY[raw]

    # Clean intermediate whitespace (e.g. "React   JS" -> "react js")
    cleaned = re.sub(r"\s+", " ", raw)
    if cleaned in ALIAS_DICTIONARY:
        return ALIAS_DICTIONARY[cleaned]

    # Remove redundant trailing words like 'developer', 'engineer', 'programming', 'language'
    trimmed = re.sub(r"\b(programming language|language|framework|library|technology|developer|engineer)\b", "", cleaned).strip()
    if trimmed in ALIAS_DICTIONARY:
        return ALIAS_DICTIONARY[trimmed]

    return trimmed if trimmed else cleaned


def get_deterministic_related_skill(job_skill: str, candidate_skill: str) -> Optional[str]:
    """
    Checks if a candidate skill is a recognized related technology to a required job skill.
    Returns the relationship description if related, or None.
    """
    norm_job = normalize_skill(job_skill)
    norm_cand = normalize_skill(candidate_skill)

    if not norm_job or not norm_cand:
        return None

    if (norm_job, norm_cand) in RELATED_SKILLS_MAP:
        return RELATED_SKILLS_MAP[(norm_job, norm_cand)]

    # Check reversed if symmetrical
    if (norm_cand, norm_job) in RELATED_SKILLS_MAP:
        return RELATED_SKILLS_MAP[(norm_cand, norm_job)]

    return None

