"""
sample_data/create_samples.py — Create sample DOCX resumes for testing.

Run from the project root:
    python sample_data/create_samples.py

Generates:
  - sample_data/sample_resume_junior.docx   (lower match)
  - sample_data/sample_resume_senior.docx   (higher match)
  - sample_data/sample_jd.txt               (job description)

All data is fictional.
"""

from pathlib import Path
from docx import Document

BASE = Path(__file__).parent

# ── Job Description ──────────────────────────────────────────────────────────
SAMPLE_JD = """Position: Senior Python Backend Engineer

We are looking for an experienced Python Backend Engineer to join our growing team.

Required Skills:
- Python (5+ years)
- Flask or FastAPI for REST API development
- SQL databases: PostgreSQL or MySQL
- Docker and container orchestration (Kubernetes a plus)
- Git version control
- Agile / Scrum methodology
- Experience with CI/CD pipelines (Jenkins, GitHub Actions)
- Amazon Web Services (AWS) or Google Cloud Platform (GCP)

Responsibilities:
- Design and develop scalable REST APIs
- Collaborate with frontend engineers on API contracts
- Write unit and integration tests (pytest)
- Participate in code reviews and architectural discussions
- Deploy and monitor services in cloud infrastructure

Nice to have:
- GraphQL API experience
- Redis caching
- Machine learning pipeline experience
- Microservices architecture
"""

# ── Junior Resume (lower expected match) ────────────────────────────────────
JUNIOR_RESUME = """Alex Johnson
alex.johnson@email.example | +1-555-0201 | github.com/alexj

Objective
Recent Computer Science graduate seeking a backend developer position.

Education
Bachelor of Science in Computer Science
Westfield University, 2023

Skills
- Programming: Python, Java, HTML, CSS
- Databases: MySQL
- Tools: Git, VS Code
- Operating Systems: Linux, Windows

Projects
Library Management System
  - Built a command-line library system in Python using SQLite
  - Implemented CRUD operations and search functionality

Student Portal Web App
  - Created a basic web portal using Python and Flask
  - Connected to a MySQL database for student record management

Work Experience
Teaching Assistant — Computer Science Department (2022–2023)
  - Helped students debug Python and Java code
  - Graded assignments and provided constructive feedback

Certifications
Python for Beginners — Coursera (2022)
"""

# ── Senior Resume (higher expected match) ───────────────────────────────────
SENIOR_RESUME = """Jordan Rivera
jordan.rivera@email.example | +1-555-0312
LinkedIn: linkedin.com/in/jordan-rivera | GitHub: github.com/jordanrivera

Summary
Senior Python Backend Engineer with 6 years of experience designing and scaling
distributed REST APIs. Proven track record of delivering high-performance microservices
using Flask, PostgreSQL, Docker, and AWS. Passionate about clean code and Agile practices.

Technical Skills
Languages    : Python, SQL, Bash, TypeScript
Frameworks   : Flask, FastAPI, SQLAlchemy, pytest
Databases    : PostgreSQL, MySQL, Redis, MongoDB
Cloud / DevOps: AWS (EC2, S3, Lambda, RDS), Docker, Kubernetes, GitHub Actions, Jenkins
Practices    : REST API design, Microservices, CI/CD, Agile, Scrum, Code Review
Other        : Git, Linux, GraphQL, Redis caching

Professional Experience

Senior Backend Engineer — DataStream Inc. (2021–2024)
  - Architected and deployed a REST API platform serving 500K+ daily requests using Flask and PostgreSQL
  - Reduced average API latency by 35% through query optimisation and Redis caching
  - Led migration from monolith to microservices, improving deployment frequency by 60%
  - Implemented CI/CD pipelines with GitHub Actions and Docker, cutting release cycle from 2 weeks to 2 days
  - Mentored 4 junior engineers; conducted weekly code reviews
  - Collaborated with AWS for infrastructure scaling on EC2 and RDS

Backend Developer — CodeForge Ltd. (2018–2021)
  - Built and maintained 10+ REST API endpoints using Python and Flask
  - Designed and optimised SQL schemas for PostgreSQL and MySQL
  - Integrated Docker containers and Kubernetes orchestration for staging and production
  - Worked in Agile / Scrum teams with 2-week sprints

Projects
Inventory Analytics API
  - Python, Flask, PostgreSQL, Docker — real-time inventory tracking REST API
  - Achieved 99.9% uptime with Kubernetes health checks and auto-scaling

ML Serving Pipeline
  - Deployed scikit-learn models as REST API microservices on AWS Lambda
  - Reduced model inference latency from 800ms to 120ms

Education
B.Sc. Computer Engineering, Northern Institute of Technology, 2018

Certifications
AWS Certified Solutions Architect — Associate (2022)
Docker Certified Associate (2021)
"""


def write_docx(filename: str, content: str) -> None:
    doc = Document()
    for line in content.strip().split('\n'):
        doc.add_paragraph(line)
    path = BASE / filename
    doc.save(str(path))
    print(f"Created: {path}")


if __name__ == '__main__':
    write_docx("sample_resume_junior.docx", JUNIOR_RESUME)
    write_docx("sample_resume_senior.docx", SENIOR_RESUME)

    jd_path = BASE / "sample_jd.txt"
    jd_path.write_text(SAMPLE_JD, encoding='utf-8')
    print(f"Created: {jd_path}")
    print("\nAll sample files created successfully!")
    print("Tip: Use these files to test the ATS Analyzer at http://127.0.0.1:5000")
