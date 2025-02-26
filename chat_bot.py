#!/usr/bin/env python
# coding: utf-8

# In[11]:
!pip install fitz
!pip install openai
!pip install SpeechRecognition pyaudio
!pip install mysql-connector-python

from flask import Flask, request, jsonify
import fitz  # PyMuPDF
import openai
import speech_recognition as sr
import mysql.connector

app = Flask(__name__)

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"
    return text

def ask_question(pdf_text, question):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "You are an assistant answering questions from documents."},
                  {"role": "user", "content": f"Document: {pdf_text}\n\nQuestion: {question}"}]
    )
    return response["choices"][0]["message"]["content"]

def speech_to_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Speak your question:")
        audio = recognizer.listen(source)
    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return "Could not understand the audio."
    except sr.RequestError:
        return "Speech recognition service unavailable."

def store_in_database(pdf_text, question, answer):
    conn = mysql.connector.connect(
        host="localhost",  # Change this if your MySQL server is remote
        user="your_username",  # Replace with your MySQL username
        password="your_password",  # Replace with your MySQL password
        database="chatbot_db"  # Replace with your MySQL database name
    )
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS qa (
            id INT AUTO_INCREMENT PRIMARY KEY,
            document TEXT,
            question TEXT,
            answer TEXT
        )
    """)
    cursor.execute("INSERT INTO qa (document, question, answer) VALUES (%s, %s, %s)", (pdf_text, question, answer))
    conn.commit()
    conn.close()

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    pdf_path = data.get("pdf_path")
    question = data.get("question")
    pdf_text = extract_text_from_pdf(pdf_path)
    answer = ask_question(pdf_text, question)
    store_in_database(pdf_text, question, answer)
    return jsonify({"question": question, "answer": answer})

@app.route("/speech", methods=["GET"])
def speech():
    question = speech_to_text()
    if question == "Speech recognition service unavailable." or question == "Could not understand the audio.":
        return jsonify({"error": question})
    return jsonify({"question": question})

if __name__ == "__main__":
    app.run(debug=True)

