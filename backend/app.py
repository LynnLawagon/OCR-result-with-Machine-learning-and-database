from flask import Flask, request, jsonify, render_template
import cv2
import easyocr
import re
import numpy as np
import io
import os
from datetime import datetime
import mysql.connector

app = Flask(__name__, template_folder='templates')

# EasyOCR setup
reader = easyocr.Reader(['en'], gpu=False)

# MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",            
    database="db_ocr_results"
)
cursor = db.cursor()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    # Save uploaded image
    uploads_dir = os.path.join("static", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    img_path = os.path.join(uploads_dir, file.filename)
    file.save(img_path)
    img_path_db = os.path.join("uploads", file.filename)

    # Convert file to OpenCV image for OCR
    in_memory_file = io.BytesIO()
    file.seek(0)
    file.save(in_memory_file)
    data = np.frombuffer(in_memory_file.getvalue(), dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)

    # OCR
    text1 = reader.readtext(img)
    texts = [text.strip() for bbox, text, score in text1 if score > 0.4]
    full_text = ' '.join(texts).upper()

    # Extract fields
    dob_match = re.search(r'(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+\d{1,2}\s+\d{4}', full_text)
    dob = dob_match.group(0) if dob_match else None
    dob_mysql = None
    if dob:
        try:
            dob_mysql = datetime.strptime(dob, "%B %d %Y").date()
        except ValueError:
            dob_mysql = None

    last_name_match = re.search(r'APELYIDO/ LAST NAME\s+([A-Z\s]+?)(?=\sMGA PANGALAN/)', full_text)
    last_name = last_name_match.group(1).strip() if last_name_match else ""

    first_name_match = re.search(r'MGA PANGALAN/ GIVEN NAMES\s+([A-Z\s]+?)(?=\sGITNANG APELYIDO/)', full_text)
    first_name = first_name_match.group(1).strip() if first_name_match else ""

    middle_name_match = re.search(r'GITNANG APELYIDO/.*?Middle Name\s*([A-Z\s]+?)(?=\sPETSA NG)', full_text, flags=re.IGNORECASE)
    middle_name = middle_name_match.group(1).strip() if middle_name_match else ""

    address_match = re.search(r'TIRAHAN/ADDRESS\s+(.+)', full_text, flags=re.IGNORECASE)
    address = address_match.group(1).strip() if address_match else ""

    return jsonify({
        "ID_type": "", 
        "First_name": first_name,
        "Middle_name": middle_name,
        "Last_name": last_name,
        "Date_of_birth": dob_mysql.strftime("%Y-%m-%d") if dob_mysql else "",
        "Address": address,
        "Img_path": img_path_db
    })


@app.route('/save_guest', methods=['POST'])
def save_guest():
    data = request.json

    dob =data.get("Date_of_birth")
    if dob == "":
        dob = None 

    sql = """
    INSERT INTO tbl_guests
    (ID_type, First_name, Middle_name, Last_name, Date_of_birth, Address, Img_path)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """ 
    values = (
        data.get("ID_type", ""),
        data.get("First_name", ""),
        data.get("Middle_name", ""),
        data.get("Last_name", ""),
        dob,
        data.get("Address", ""),
        data.get("Img_path", "")
    )

    cursor.execute(sql, values)
    db.commit()
    guest_id = cursor.lastrowid
    return jsonify({"status": "success", "guest_id": guest_id})


if __name__ == "__main__":
    app.run(debug=True)
