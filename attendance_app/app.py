import traceback

from flask import Flask, render_template, request, jsonify
import os
from datetime import datetime
import sqlite3
import base64
from utils.face_utils import is_face_already_registered, recognize_face

app = Flask(__name__)

# Ensure folder exists
os.makedirs('faces', exist_ok=True)

# Database setup
def init_db():
    with sqlite3.connect("database.db") as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS employees (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            face_path TEXT NOT NULL
                        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS attendance (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            emp_id INTEGER,
                            date TEXT,
                            time TEXT
                        )''')
init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/attendance')
def attendance_page():
    return render_template('attendance.html')

@app.route('/report')
def report_page():
    return render_template('report.html')

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    try:
        data = request.get_json()
        image_data = data['image'].split(',')[1]
        lat = data.get('lat')
        long = data.get('long')
        img_path = f"temp_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"

        # Save temp image
        with open(img_path, "wb") as f:
            f.write(base64.b64decode(image_data))

        # Recognize face
        name = recognize_face(img_path)
        os.remove(img_path)

        if not name:
            return jsonify({
                "success": False,
                "message": "Face not recognized. Please try again."
            })

        date_today = datetime.now().strftime('%Y-%m-%d')
        time_now = datetime.now().strftime('%H:%M:%S')

        with sqlite3.connect("database.db") as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM employees WHERE name=?", (name,))
            emp = cur.fetchone()

            if emp:
                emp_id = emp[0]
                # ✅ Allow multiple entries (no duplicate check)
                cur.execute("""
                    INSERT INTO attendance (emp_id, date, time, latitude, longitude)
                    VALUES (?, ?, ?, ?, ?)
                """, (emp_id, date_today, time_now, lat, long))
                conn.commit()

        return jsonify({
            "success": True,
            "message": f"Attendance marked for {name} at {time_now} (Lat: {lat:.5f}, Long: {long:.5f})."
        })

    except Exception as e:
        print("❌ Error:", e)
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500

@app.route('/save_face', methods=['POST'])
def save_face():
    try:
        data = request.get_json()
        name = data['name']
        image_data = data['image'].split(',')[1]
        temp_path = f"temp_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"

        # Save temporary image
        with open(temp_path, "wb") as f:
            f.write(base64.b64decode(image_data))

        # Check if face already exists
        already_registered, existing_name = is_face_already_registered(temp_path)

        if already_registered:
            os.remove(temp_path)
            return jsonify({
                "message": f"This face is already registered as '{existing_name}'."
            })

        # Save as new face
        img_path = f"faces/{name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        os.rename(temp_path, img_path)

        with sqlite3.connect("database.db") as conn:
            conn.execute("INSERT INTO employees (name, face_path) VALUES (?, ?)", (name, img_path))
            conn.commit()

        return jsonify({"message": "Employee registered successfully!"})
    except:
        print(traceback.format_exc())

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5051, debug=True)import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

