import streamlit as st
import re
from collections import Counter
import pandas as pd
from docx import Document
import PyPDF2
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Setup
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

# Helper functions
def extract_text_from_pdf(pdf_file):
    text = ""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def extract_text_from_docx(docx_file):
    text = ""
    doc = Document(docx_file)
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def clean_and_tokenize(text):
    text = text.lower()
    tokens = re.findall(r'\b[a-z]+\b', text)
    cleaned = [lemmatizer.lemmatize(t) for t in tokens if t not in stop_words]
    return cleaned

def analyze_keywords(resume_text, jd_text):
    resume_tokens = set(clean_and_tokenize(resume_text))
    jd_tokens_list = clean_and_tokenize(jd_text)
    jd_tokens = set(jd_tokens_list)

    matched = sorted(list(resume_tokens & jd_tokens))
    missing = sorted(list(jd_tokens - resume_tokens))
    score = round(len(matched)/len(jd_tokens)*100, 2) if jd_tokens else 0
    jd_counts = Counter(jd_tokens_list)
    jd_top = jd_counts.most_common(20)

    return matched, missing, score, jd_top

# Streamlit UI
st.title("Resume Keyword Analyzer")
st.write("Upload your resume and job description to analyze keyword match.")

resume_file = st.file_uploader("Upload Resume (PDF/DOCX/TXT)", type=['pdf','docx','txt'])
jd_file = st.file_uploader("Upload Job Description (TXT) or paste text", type=['txt'])

jd_text_area = st.text_area("Or paste job description text here:")

if st.button("Analyze"):
    if resume_file is None:
        st.warning("Please upload a resume!")
    else:
        # Read resume
        resume_text = ""
        if resume_file.name.lower().endswith(".pdf"):
            resume_text = extract_text_from_pdf(resume_file)
        elif resume_file.name.lower().endswith(".docx"):
            resume_text = extract_text_from_docx(resume_file)
        else:
            resume_text = resume_file.read().decode("utf-8")

        # Read JD
        jd_text = ""
        if jd_file is not None and jd_file.name.lower().endswith(".txt"):
            jd_text = jd_file.read().decode("utf-8")
        elif jd_text_area.strip() != "":
            jd_text = jd_text_area.strip()
        else:
            st.warning("Please upload job description or paste text!")
            jd_text = ""

        if jd_text:
            matched, missing, score, jd_top = analyze_keywords(resume_text, jd_text)
            st.success(f"Match Score: {score}%")
            st.write(f"Matched Keywords ({len(matched)}): {', '.join(matched[:50])}")
            st.write(f"Missing Keywords ({len(missing)}): {', '.join(missing[:50])}")

            df_missing = pd.DataFrame(missing, columns=["missing_keyword"])
            st.download_button("Download Missing Keywords CSV", df_missing.to_csv(index=False), "missing_keywords.csv")
            
            st.write("Top JD keywords:")
            for k, c in jd_top:
                st.write(f"{k}: {c}")
