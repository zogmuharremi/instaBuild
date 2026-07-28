import os, json
from datetime import datetime
from flask import Flask, render_template, request, jsonify

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'), static_folder=os.path.join(BASE_DIR, 'images'), static_url_path='/images')
app.secret_key = os.environ.get('SECRET_KEY', 'instabuild-2026')

SUBMISSIONS_FILE = os.path.join(BASE_DIR, 'submissions.json')

def save_submission(data):
    subs = []
    if os.path.exists(SUBMISSIONS_FILE):
        with open(SUBMISSIONS_FILE) as f:
            subs = json.load(f)
    subs.append(data)
    with open(SUBMISSIONS_FILE, 'w') as f:
        json.dump(subs, f, indent=2, default=str)

@app.context_processor
def inject_nav():
    return {'nav_items': [
        ('/', 'Home'),
        ('/about', 'About'),
        ('/solutions', 'Solutions'),
        ('/builder', '3D Builder'),
        ('/contact', 'Contact'),
    ]}

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/solutions')
def solutions():
    return render_template('solutions.html')

@app.route('/builder')
def builder():
    return render_template('builder.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/api/contact', methods=['POST'])
def api_contact():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    msg = request.form.get('message', '').strip()
    if not name or not email or not msg:
        return jsonify({'success': False, 'error': 'Name, email, and message required.'}), 400
    save_submission({
        'name': name, 'email': email,
        'phone': request.form.get('phone', '').strip(),
        'project_type': request.form.get('project_type', '').strip(),
        'message': msg, 'timestamp': datetime.now().isoformat()
    })
    return jsonify({'success': True, 'message': 'Thank you! We\'ll be in touch within 24 hours.'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
