from flask import Flask, render_template, request, redirect, send_file
import csv
from datetime import datetime
import os
from fpdf import FPDF
from pydub import AudioSegment
import whisper
from transformers import pipeline

app = Flask(__name__)

# Load Whisper model only once
model = whisper.load_model("base")

question_generator = pipeline(
    "text2text-generation",
    model="valhalla/t5-base-qg-hl"
)

os.makedirs("uploads", exist_ok=True)


# HOME
@app.route('/')
def home():
    return redirect('/login')


# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form.get('username')
        password = request.form.get('password')

        if username == "admin" and password == "1234":
            return redirect('/dashboard')

        return "Wrong username or password ❌"

    return render_template('login.html')


# DASHBOARD
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


# ATTENDANCE
@app.route('/attendance', methods=['GET', 'POST'])
def attendance():

    if request.method == 'POST':

        student_name = request.form.get('student_name')
        status = request.form.get('status')

        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open("attendance.csv", "a", newline='') as file:

            writer = csv.writer(file)
            writer.writerow([student_name, status, time])

        return "Attendance Saved ✅"

    return render_template("attendance.html")


# VIEW ATTENDANCE
@app.route('/view')
def view():

    data = []

    if os.path.exists("attendance.csv"):

        with open("attendance.csv", "r") as file:
            reader = csv.reader(file)
            data = list(reader)

    return render_template("view.html", data=data)
# AUDIO UPLOAD
@app.route('/upload_audio', methods=['GET', 'POST'])
def upload_audio():

    if request.method == 'POST':

        file = request.files['audio']

        if file.filename == '':
            return "No file selected ❌"

        path = os.path.join("uploads", file.filename)
        file.save(path)

        try:

            # Convert audio to WAV
            sound = AudioSegment.from_file(path)
            wav_path = "uploads/temp.wav"
            sound.export(wav_path, format="wav")

            # Speech to Text
            result = model.transcribe(
                wav_path,
                language="en",
                fp16=False
            )

            text = result["text"]

            # Summary
            sentences = text.split('.')
            summary = '. '.join(sentences[:5])

            # AI Quiz
            quiz = ""

            for sentence in sentences[:5]:

                sentence = sentence.strip()

                if sentence:

                    try:

                        output = question_generator(
                            "generate question: " + sentence,
                            max_length=64,
                            do_sample=False
                        )

                        quiz += output[0]["generated_text"] + "\n\n"

                    except:
                        pass

            # Save transcript
            with open("uploads/notes.txt", "w", encoding="utf-8") as f:
                f.write(text)

            return f"""
<h2>Full Text</h2>

<textarea rows="10" cols="100">
{text}
</textarea>

<h2>Summary</h2>

<textarea rows="5" cols="100">
{summary}
</textarea>

<h2>Quiz</h2>

<textarea rows="10" cols="100">
{quiz}
</textarea>

<br><br>

<a href="/generate_notes">Generate PDF Notes</a>

<br><br>

<a href="/download_notes">Download PDF</a>
"""

        except Exception as e:
            return f"Error: {str(e)}"

    return render_template("upload.html")
           
@app.route('/summary')
def summary():

    if not os.path.exists("uploads/notes.txt"):
        return "Upload audio first ❌"

    with open("uploads/notes.txt", "r", encoding="utf-8") as f:
        text = f.read()

    sentences = text.split('.')
    summary = '. '.join(sentences[:5])

    return render_template(
        "summary.html",
        summary=summary
    )

# LOGOUT
@app.route('/logout')
def logout():
    return redirect('/login')


# GENERATE PDF NOTES
@app.route('/generate_notes')
def generate_notes():

    if not os.path.exists("uploads/notes.txt"):
        return "Upload audio first ❌"

    with open("uploads/notes.txt", "r", encoding="utf-8") as f:
        text = f.read()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.multi_cell(0, 10, text)

    pdf.output("uploads/notes.pdf")

    return "Notes PDF Generated Successfully ✅"


# DOWNLOAD PDF
@app.route('/download_notes')
def download_notes():

    return send_file(
        "uploads/notes.pdf",
        as_attachment=True
    )


if __name__ == '__main__':
    app.run(debug=True)
    