import streamlit as st
import json
import pandas as pd
from utils import *

# ------------------- PAGE CONFIG -------------------
st.set_page_config(page_title="HireMatch AI", layout="wide")

# ------------------- STYLING -------------------
st.markdown("""
<style>
body { background-color: #f8fafc; }

.card {
    background-color: #ffffff;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 15px;
    border: 1px solid #e2e8f0;
}

h1, h2, h3 { color: #1e293b; }

p { color: #334155; }

.high { color: #16a34a; font-weight: bold; }
.medium { color: #ca8a04; font-weight: bold; }
.low { color: #dc2626; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


# ------------------- TITLE -------------------
st.markdown("<h1 style='text-align:center; color:#2563eb;'>🚀 HireMatch AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>AI-Powered Intelligent Hiring Dashboard</p>", unsafe_allow_html=True)

# ------------------- LOAD DATA -------------------
with open("data/job_descriptions.json") as f:
    jobs = json.load(f)

with open("data/resumes.json") as f:
    candidates = json.load(f)

# ------------------- SIDEBAR -------------------
st.sidebar.header("⚙️ Recruiter Preferences")

roles = [job["role"] for job in jobs]
selected_role = st.sidebar.selectbox("💼 Select Role", roles)

min_exp = st.sidebar.slider("📅 Minimum Experience", 0, 5, 0)
min_score = st.sidebar.slider("🎯 Minimum Score", 0, 100, 50)

priority = st.sidebar.selectbox(
    "⭐ What matters most?",
    ["Balanced", "Skills", "Projects", "Experience", "Certifications"]
)

job = next(j for j in jobs if j["role"] == selected_role)

st.sidebar.markdown("### 📄 Job Description")
st.sidebar.write(job["responsibilities"])

# ------------------- FILE UPLOAD -------------------
uploaded_files = st.file_uploader(
    "📄 Upload Additional Resumes (PDF)",
    accept_multiple_files=True
)

# ------------------- ANALYZE -------------------
if st.button("🚀 Analyze & Rank Candidates"):

    all_candidates = candidates.copy()

    # Add uploaded PDFs
    if uploaded_files:
        for file in uploaded_files:
            resume_text = extract_text_from_pdf(file)

            all_candidates.append({
                "name": file.name,
                "skills": [],
                "projects": [],
                "experience_years": 0,
                "certifications": [],
                "resume_text": resume_text
            })

    results = []
    job_text = job_to_text(job)
    skill_gaps_all = []

    # ------------------- LOOP -------------------
    for c in all_candidates:

        if c["experience_years"] < min_exp:
            continue

        # Handle JSON vs PDF
        if "resume_text" in c:
            resume_text = c["resume_text"]
        else:
            resume_text = resume_to_text(c)

        # ------------------- SCORING -------------------
        semantic_score = get_score(job_text, resume_text)

        missing = get_missing(job["required_skills"], c["skills"])
        matched = list(set(job["required_skills"]) & set(c["skills"]))

        skill_score = (len(matched) / len(job["required_skills"])) * 100 if job["required_skills"] else 0

        exp_score = min(
            c["experience_years"] / job["experience_years"], 1
        ) * 100 if job["experience_years"] > 0 else 100

        proj_score = project_score(c)
        cert_score = len(c["certifications"]) * 20

        # ------------------- DYNAMIC WEIGHTS -------------------
        w_sem, w_skill, w_exp, w_proj, w_cert = 0.4, 0.3, 0.2, 0.05, 0.05

        if priority == "Skills":
            w_skill += 0.2
        elif priority == "Projects":
            w_proj += 0.2
        elif priority == "Experience":
            w_exp += 0.2
        elif priority == "Certifications":
            w_cert += 0.2

        total = w_sem + w_skill + w_exp + w_proj + w_cert
        w_sem, w_skill, w_exp, w_proj, w_cert = [
            w/total for w in [w_sem, w_skill, w_exp, w_proj, w_cert]
        ]

        final_score = round(
            (w_sem * semantic_score +
             w_skill * skill_score +
             w_exp * exp_score +
             w_proj * proj_score +
             w_cert * cert_score),
            2
        )

        explanation = generate_rationale(final_score, matched, missing)
        if final_score < 65:
            growth = get_growth_path(missing, c)
        else:
            growth = []

        skill_gaps_all.extend(missing)

        results.append({
            "name": c["name"],
            "score": final_score,
            "semantic": semantic_score,
            "skills": skill_score,
            "experience": exp_score,
            "rationale": explanation,
            "missing": missing,
            "growth": growth
        })

    # ------------------- SORT + FILTER -------------------
    # Sort all results first
    results = sorted(results, key=lambda x: x["score"], reverse=True)

# Create full dataframe BEFORE filtering
    df_full = pd.DataFrame(results)

# Apply filter separately
    filtered_results = [r for r in results if r["score"] >= min_score]

    df_filtered = pd.DataFrame(filtered_results)

    if not results:
        st.warning("No candidates match the selected filters.")
        st.stop()

    # ------------------- HEADER -------------------
    st.subheader(f"🏆 Top Candidates for {selected_role}")
    st.info(f"⭐ Recruiter Priority: {priority}")

    # ------------------- METRICS -------------------
    col1, col2, col3 = st.columns(3)
    col1.metric("👥 Total Candidates", len(results))
    col2.metric("🏆 Best Score", f"{int(max(df_full['score']))}%")
    col3.metric("📊 Avg Score", f"{int(sum([r['score'] for r in results]) / len(results))}%")

    # ------------------- CHART -------------------
    df = df_filtered
    results = filtered_results
    st.bar_chart(df.set_index("name")["score"])

    # ------------------- TABLE -------------------
    st.dataframe(df[["name", "score", "skills", "experience"]])

    # ------------------- DOWNLOAD -------------------
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Results", csv, "results.csv")

    # ------------------- CARDS -------------------
    for r in results[:5]:
        score = int(r['score'])

        if score > 75:
            score_class = "high"
            emoji = "🟢"
        elif score > 50:
            score_class = "medium"
            emoji = "🟡"
        else:
            score_class = "low"
            emoji = "🔴"

        st.markdown(f"""
        <div class="card">
            <h3>👤 {r['name']}</h3>
            <h2 class="{score_class}">{emoji} {score}% Match</h2>
            <p><b>🧠 Rationale:</b> {r['rationale']}</p>
            <p><b>⚠️ Missing Skills:</b> {', '.join(r['missing'])}</p>
        </div>
        """, unsafe_allow_html=True)
        if r["growth"]:
            st.success(f"🚀 Growth Path: {', '.join(r['growth'])}")

        st.progress(score)

    # ------------------- SKILL GAP -------------------
    st.subheader("📉 Most Missing Skills")

    if skill_gaps_all:
        gap_series = pd.Series(skill_gaps_all).value_counts().head(5)
        st.bar_chart(gap_series)