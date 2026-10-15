from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import io
from pypdf import PdfReader

app = FastAPI(
    title="HireAI Fresh",
    description="AI-powered resume analysis and job matching system",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Common tech skills dictionary to scan for in resumes and job descriptions
COMMON_SKILLS = [
    "python", "fastapi", "flask", "django", "javascript", "html", "css", 
    "sql", "postgresql", "mysql", "mongodb", "git", "docker", "aws", 
    "machine learning", "ai", "react", "node.js", "c++", "java", "rest apis",
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "problem solving"
]

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extracts all text from uploaded PDF bytes using pypdf."""
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read PDF file: {str(e)}")

def analyze_skills(resume_text: str, job_desc: str):
    """Compares resume text against job description keywords."""
    resume_lower = resume_text.lower()
    job_lower = job_desc.lower()

    # Find which common skills appear in the job description
    required_skills = [skill for skill in COMMON_SKILLS if skill in job_lower]
    if not required_skills:
        # Fallback if specific tech keywords aren't matched
        required_skills = ["python", "problem solving", "communication", "git"]

    # Find which required skills are present in the resume
    matched_skills = [skill for skill in required_skills if skill in resume_lower]
    
    # Find gaps (missing skills)
    missing_skills = [skill for skill in required_skills if skill not in resume_lower]

    # Find general skills found in the resume
    resume_found_skills = [skill for skill in COMMON_SKILLS if skill in resume_lower]
    if not resume_found_skills:
        resume_found_skills = ["General Technical Skills"]

    # Calculate match percentage score
    if len(required_skills) > 0:
        score = int((len(matched_skills) / len(required_skills)) * 100)
    else:
        score = 75

    # Generate custom recommendations
    recommendations = []
    if missing_skills:
        recommendations.append(f"Consider adding or highlighting experience with: {', '.join(missing_skills).title()}.")
    recommendations.append("Ensure your project section explicitly demonstrates measurable impact or outcomes.")
    recommendations.append("Keep your formatting clean and consistent with standard engineering resume layouts.")

    # Generate interview questions based on required skills
    questions = [
        f"Can you explain a project where you utilized {required_skills[0].title()}?",
        "How do you approach debugging complex errors or bottlenecks in your code?",
        "Describe a time you collaborated with a team to deliver a technical feature under a deadline."
    ]

    return score, resume_found_skills, matched_skills, missing_skills, recommendations, questions

@app.get("/")
def home():
    return {"status": "online", "message": "HireAI Backend is operational!"}

@app.post("/api/analyze-resume")
async def analyze_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded PDF is empty.")

    # Extract actual text from uploaded PDF
    resume_text = extract_text_from_pdf(file_bytes)

    if len(resume_text.strip()) < 20:
        raise HTTPException(status_code=400, detail="The uploaded PDF appears to be scanned or contains no readable text.")

    # Run analysis
    score, resume_skills, matched_skills, missing_skills, recommendations, questions = analyze_skills(resume_text, job_description)

    return {
        "status": "success",
        "message": "Resume analyzed successfully!",
        "final_match_score": score,
        "resume_skills": [s.title() for s in resume_skills],
        "matched_skills": [s.title() for s in matched_skills],
        "missing_skills": [s.title() for s in missing_skills],
        "recommendations": recommendations,
        "interview_questions": questions
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)