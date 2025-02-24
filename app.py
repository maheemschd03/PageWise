from flask import Flask, render_template, request, send_file
import os
from pdfminer.high_level import extract_text
import google.generativeai as genai
from pdfminer.pdfparser import PDFSyntaxError

# Initialize Flask app
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
SUMMARY_FOLDER = 'summaries'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SUMMARY_FOLDER'] = SUMMARY_FOLDER

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SUMMARY_FOLDER, exist_ok=True)

# Configure Gemini AI
genai.configure(api_key="AIzaSyCGRagRWD_XWzdlR6ZGgJfyeKZM6agwMw4")


def summarize(text):
    """
    Summarizes and cleans the given text using Gemini AI.
    """
    try:
        prompts = [
            f"Please elaborate and explain this text clearly: {text}",
            "Now, clean the explanation and present it in a readable format."
        ]

        # Generate elaboration
        model = genai.GenerativeModel('gemini-2.0-flash')
        explanation = model.generate_content(prompts[0]).text.strip()

        # Clean and format the explanation
        summary = model.generate_content(f"{prompts[1]} Text: {explanation}").text.strip()
        return summary

    except Exception as e:
        return f"Error during summarization: {str(e)}"


def count_pages(filepath):
    """
    Counts the number of pages in the PDF.
    """
    try:
        text = extract_text(filepath)
        pages = text.split('\x0c')  # '\x0c' is a form feed character indicating page breaks
        return len(pages) - 1  # Last split may be empty
    except PDFSyntaxError:
        return 0


def extract_and_summarize_pdf(filepath, num_pages=None):
    """
    Extracts text from PDF and summarizes it page by page.
    """
    summaries = ""
    try:
        total_pages = count_pages(filepath)
        num_pages = min(num_pages or total_pages, total_pages)

        for page_number in range(num_pages):
            text = extract_text(filepath, page_numbers=[page_number])
            if text.strip():
                summary = summarize(text)
                summaries += f"--- Page {page_number + 1} ---\n{summary}\n\n"

        # Save summarized text to a file
        summary_file = os.path.join(app.config['SUMMARY_FOLDER'], "summarized_text.txt")
        with open(summary_file, "w") as file:
            file.write(summaries)

        return summaries, summary_file
    except Exception as e:
        return f"Error: {str(e)}", None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    if 'pdf' not in request.files:
        return "No file part"

    file = request.files['pdf']
    num_pages = request.form.get('num_pages', type=int)

    if file.filename == '':
        return "No selected file"

    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        # Extract and summarize PDF
        summaries, summary_file = extract_and_summarize_pdf(filepath, num_pages)
        return render_template('result.html', text=summaries, download_link=summary_file)


@app.route('/download')
def download():
    filepath = os.path.join(app.config['SUMMARY_FOLDER'], "summarized_text.txt")
    return send_file(filepath, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
