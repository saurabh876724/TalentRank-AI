"""Generate 10 synthetic sample resumes (5 PDF + 5 DOCX) in sample_resumes/.

All identities and contact details are fictional.
Run from the project root:  python scripts/generate_sample_resumes.py
"""
import sys
from pathlib import Path

import pymupdf
from docx import Document

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "sample_resumes"

CANDIDATES = [
    {
        "name": "Aarav Sharma", "email": "aarav.sharma@example.com", "phone": "+91 98765 43210",
        "skills": "Python, SQL, FastAPI, Docker, Git, Machine Learning",
        "degree": "B.Tech in Computer Science", "college": "Pune Institute of Technology", "year": "2022",
        "experience": "2 years of experience as a backend developer at FakeSoft Systems.",
    },
    {
        "name": "Meera Iyer", "email": "meera.iyer@example.com", "phone": "+91 98220 11223",
        "skills": "Java, SQL, Django, AWS, Git",
        "degree": "MCA", "college": "Chennai College of Engineering", "year": "2021",
        "experience": "3 years of experience in enterprise application development.",
    },
    {
        "name": "Rohan Verma", "email": "rohan.verma@example.com", "phone": "98111 44556",
        "skills": "JavaScript, React, HTML, CSS, Node.js, Git",
        "degree": "BCA", "college": "Delhi University", "year": "2023",
        "experience": "1 year of experience building frontend applications.",
    },
    {
        "name": "Ananya Deshpande", "email": "ananya.d@example.com", "phone": "+91 90040 77889",
        "skills": "Python, Machine Learning, Deep Learning, TensorFlow, NLP, Pandas",
        "degree": "M.Tech in Artificial Intelligence", "college": "Hyderabad Institute of Technology", "year": "2020",
        "experience": "4.5 years of experience in applied machine learning.",
    },
    {
        "name": "Karthik Nair", "email": "karthik.nair@example.com", "phone": "+91 99887 66554",
        "skills": "C++, Python, SQL, Docker, Kubernetes, Git",
        "degree": "B.E. in Information Technology", "college": "Kochi School of Engineering", "year": "2019",
        "experience": "5 years of experience in systems and platform engineering.",
    },
    {
        "name": "Priya Kulkarni", "email": "priya.kulkarni@example.com", "phone": "98230 12345",
        "skills": "Python, Flask, SQL, HTML, CSS, Git",
        "degree": "B.Sc in Computer Science", "college": "Mumbai University", "year": "2024",
        "experience": None,
    },
    {
        "name": "Vikram Singh", "email": "vikram.singh@example.com", "phone": "+91 97654 32109",
        "skills": "Java, C++, SQL, AWS, Docker",
        "degree": "B.Tech in Electronics and Communication", "college": "Jaipur National College", "year": "2018",
        "experience": "6 years of experience across backend and cloud infrastructure.",
    },
    {
        "name": "Sneha Reddy", "email": "sneha.reddy@example.com", "phone": "+91 96543 21098",
        "skills": "Python, PyTorch, Deep Learning, NLP, Scikit-learn, NumPy",
        "degree": "M.Sc in Data Science", "college": "Bengaluru Institute of Science", "year": "2022",
        "experience": "2.5 years of experience as a data scientist at MockAnalytics.",
    },
    {
        "name": "Arjun Menon", "email": "arjun.menon@example.com", "phone": "95432 10987",
        "skills": "JavaScript, React, FastAPI, MongoDB, Git, REST API",
        "degree": "B.Tech in Computer Engineering", "college": "Goa College of Engineering", "year": "2023",
        "experience": "1.5 years of experience in full-stack development.",
    },
    {
        "name": "Divya Bhatt", "email": "divya.bhatt@example.com", "phone": "+91 94321 09876",
        "skills": "Python, SQL, Machine Learning, AWS, Git, TensorFlow",
        "degree": "MBA in Information Systems", "college": "Ahmedabad Management University", "year": "2017",
        "experience": "7 years of experience leading analytics teams.",
    },
]


def resume_lines(candidate: dict) -> list[str]:
    lines = [
        candidate["name"],
        f"Email: {candidate['email']} | Phone: {candidate['phone']}",
        "",
        "SKILLS",
        candidate["skills"],
        "",
        "EDUCATION",
        f"{candidate['degree']}, {candidate['college']}, {candidate['year']}",
        "",
        "EXPERIENCE",
        candidate["experience"] or "Fresher seeking entry-level opportunities.",
    ]
    return lines


def write_pdf(path: Path, lines: list[str]) -> None:
    doc = pymupdf.open()
    page = doc.new_page()
    y = 72
    for line in lines:
        if line:
            page.insert_text((72, y), line, fontsize=11)
        y += 18
    doc.save(path)
    doc.close()


def write_docx(path: Path, lines: list[str]) -> None:
    document = Document()
    for line in lines:
        document.add_paragraph(line)
    document.save(path)


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    for index, candidate in enumerate(CANDIDATES, start=1):
        slug = candidate["name"].lower().replace(" ", "_")
        lines = resume_lines(candidate)
        if index % 2 == 1:
            write_pdf(OUTPUT_DIR / f"{index:02d}_{slug}.pdf", lines)
        else:
            write_docx(OUTPUT_DIR / f"{index:02d}_{slug}.docx", lines)
    print(f"Generated {len(CANDIDATES)} sample resumes in {OUTPUT_DIR}")


if __name__ == "__main__":
    sys.exit(main())