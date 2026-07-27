import os
import json
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'))
app.secret_key = os.environ.get('SECRET_KEY', 'instabuild-secret-key-2026')

SUBMISSIONS_FILE = os.path.join(os.path.dirname(__file__), 'submissions.json')

def load_submissions():
    if os.path.exists(SUBMISSIONS_FILE):
        with open(SUBMISSIONS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_submission(data):
    subs = load_submissions()
    subs.append(data)
    with open(SUBMISSIONS_FILE, 'w') as f:
        json.dump(subs, f, indent=2, default=str)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/contact', methods=['POST'])
def contact():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    project_type = request.form.get('project_type', '').strip()
    message = request.form.get('message', '').strip()

    if not name or not email or not message:
        return jsonify({'success': False, 'error': 'Name, email, and message are required.'}), 400

    submission = {
        'name': name,
        'email': email,
        'phone': phone,
        'project_type': project_type,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }
    save_submission(submission)

    # Attempt email notification if SMTP configured
    smtp_host = os.environ.get('SMTP_HOST')
    if smtp_host:
        try:
            msg = MIMEText(
                f"New Contact Form Submission\n\n"
                f"Name: {name}\nEmail: {email}\nPhone: {phone}\n"
                f"Project Type: {project_type}\n\nMessage:\n{message}"
            )
            msg['Subject'] = f'New instaBuild Inquiry from {name}'
            msg['From'] = os.environ.get('SMTP_FROM', email)
            msg['To'] = os.environ.get('SMTP_TO', 'contact@instabuild.com')

            with smtplib.SMTP(smtp_host, int(os.environ.get('SMTP_PORT', 587))) as server:
                server.starttls()
                server.login(os.environ.get('SMTP_USER', ''), os.environ.get('SMTP_PASS', ''))
                server.send_message(msg)
        except Exception:
            pass  # Silent fail — submission is saved locally regardless

    return jsonify({'success': True, 'message': 'Thank you! We will get back to you within 24 hours.'})

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    app.run(host='0.0.0.0', port=8080, debug=False)
