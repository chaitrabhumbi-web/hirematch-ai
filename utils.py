import json
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Load model once
model = SentenceTransformer('all-MiniLM-L6-v2')


# Convert job JSON → text
def job_to_text(job):
    return f"""
    Role: {job['role']}
    Skills: {', '.join(job['required_skills'])}
    Responsibilities: {job['responsibilities']}
    Experience: {job['experience_years']} years
    """


# Convert resume JSON → text
def resume_to_text(candidate):
    return f"""
    Skills: {', '.join(candidate['skills'])}
    Projects: {', '.join(candidate['projects'])}
    Experience: {candidate['experience_years']} years
    Certifications: {', '.join(candidate['certifications'])}
    """


# Semantic similarity score
def get_score(job_text, resume_text):
    emb1 = model.encode([job_text])
    emb2 = model.encode([resume_text])
    score = cosine_similarity(emb1, emb2)[0][0]
    return round(score * 100, 2)


# Missing skills
def get_missing(job_skills, candidate_skills):
    return list(set(job_skills) - set(candidate_skills))


# Rationale generation
def generate_rationale(score, matched, missing):
    if score > 75:
        return f"Strong match with skills like {', '.join(matched[:2])}. Experience aligns well."
    elif score > 50:
        return f"Partial match with {', '.join(matched[:2])}, but lacks {', '.join(missing[:2])}."
    else:
        return f"Low alignment. Missing key skills like {', '.join(missing[:2])}."
import fitz  # PyMuPDF

def extract_text_from_pdf(file):
    text = ""
    doc = fitz.open(stream=file.read(), filetype="pdf")
    for page in doc:
        text += page.get_text()
    return text

def project_score(candidate):
    return min(len(candidate["projects"]) * 20, 100)
def get_growth_path(missing_skills, candidate):
    suggestions = []

    # Priority 1: Missing skills
    for skill in missing_skills[:2]:
        suggestions.append(f"Learn {skill}")

    # If less missing skills, suggest projects
    if len(suggestions) < 2:
        if len(candidate["projects"]) < 2:
            suggestions.append("Build more real-world projects")

    # If still less, suggest certifications
    if len(suggestions) < 2:
        if len(candidate["certifications"]) == 0:
            suggestions.append("Complete relevant certifications")

    return suggestions[:2]