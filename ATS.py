import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from google import genai
import PyPDF2

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Note: The API key should ideally be in an environment variable
client = genai.Client(api_key="YOUR API")

app = Flask(__name__)
# Enable CORS for cross-origin requests
CORS(app)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() or ""
    except Exception as e:
        print(f"Error extracting PDF: {e}")
    return text

def analyze_resume_vs_jd(resume_text, jd_text):
    prompt = f"""
    You are an expert ATS (Applicant Tracking System) and Career Coach.
    
    Job Description:
    {jd_text}
    
    Resume:
    {resume_text}
    
    Please perform a detailed analysis and provide:
    1. Match Score (0-100): A numerical score indicating how well the candidate fits the role.
    2. Analysis Summary: A brief overview of the fit.
    3. Key Strengths: What makes this candidate a good fit?
    4. Improvements Needed: Specific areas where the resume or candidate profile can be enhanced.
    5. Missing Critical Skills: Skills mentioned in JD but missing in Resume.
    6. Quality Discussion: A discussion on whether the candidate's professional qualities match the company's needs.

    Format your response clearly with headers and bullet points.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error during analysis: {str(e)}"

@app.route("/analyze", methods=["POST"])
def analyze():
    if "resume" not in request.files:
        return jsonify({"error": "Resume PDF required"}), 400

    resume_file = request.files["resume"]
    jd_text = request.form.get("job_description")

    if not jd_text:
        return jsonify({"error": "Job description required"}), 400

    if resume_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    pdf_path = os.path.join(app.config["UPLOAD_FOLDER"], resume_file.filename)
    resume_file.save(pdf_path)

    resume_text = extract_text_from_pdf(pdf_path)
    
    if not resume_text.strip():
        return jsonify({"error": "Could not extract text from the PDF. Please ensure it's a text-based PDF."}), 400

    analysis_result = analyze_resume_vs_jd(resume_text, jd_text)

    return jsonify({
        "analysis": analysis_result
    })

if __name__ == "__main__":
    app.run(debug=True, port=8080)
