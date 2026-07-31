import os, json, uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=BASE_DIR,
    static_url_path=''
)
app.secret_key = os.environ.get('SECRET_KEY', 'instabuild-2026')

# Supabase setup
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print('[instaBuild] Supabase connected')
    except ImportError:
        print('[instaBuild] Install supabase: pip install supabase')
    except Exception as e:
        print(f'[instaBuild] Supabase error: {e}')
else:
    print('[instaBuild] No SUPABASE_URL/KEY set — saving to local JSON instead')

PROJECTS_FILE = os.path.join(BASE_DIR, 'projects.json')
SUBMISSIONS_FILE = os.path.join(BASE_DIR, 'submissions.json')

# ─── HELPERS ───
def read_json(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []

def write_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def get_user_id():
    """Simple user ID from cookie or generate one"""
    uid = request.cookies.get('instabuild_uid')
    if not uid:
        uid = str(uuid.uuid4())
    return uid

# ─── ROUTES ───
@app.route('/')
def home():
    return app.send_static_file('index.html')

@app.route('/simulator')
def simulator():
    return app.send_static_file('simulator.html')

@app.route('/api/contact', methods=['POST'])
def api_contact():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    msg = request.form.get('message', '').strip()
    if not name or not email or not msg:
        return jsonify({'success': False, 'error': 'Name, email, and message required.'}), 400
    sub = {
        'name': name, 'email': email,
        'phone': request.form.get('phone', '').strip(),
        'project_type': request.form.get('project_type', '').strip(),
        'message': msg, 'timestamp': datetime.now().isoformat()
    }
    if supabase:
        try:
            supabase.table('submissions').insert(sub).execute()
        except Exception as e:
            print(f'[Supabase] submission insert error: {e}')
    else:
        subs = read_json(SUBMISSIONS_FILE)
        subs.append(sub)
        write_json(SUBMISSIONS_FILE, subs)
    return jsonify({'success': True, 'message': 'Thank you! We\'ll be in touch within 24 hours.'})

# ─── PROJECT SAVE/LOAD API ───
@app.route('/api/projects', methods=['POST'])
def save_project():
    """Save a project — stores placed items + metadata"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    uid = get_user_id()
    project = {
        'user_id': uid,
        'name': data.get('name', 'Untitled'),
        'items': data.get('items', []),
        'total_cost': data.get('total_cost', 0),
        'budget': data.get('budget', 100000),
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }

    project_id = data.get('id')
    try:
        if supabase:
            if project_id:
                supabase.table('projects').update(project).eq('id', project_id).execute()
            else:
                result = supabase.table('projects').insert(project).execute()
                if result.data:
                    project_id = result.data[0].get('id')
        else:
            projects = read_json(PROJECTS_FILE)
            if project_id:
                for i, p in enumerate(projects):
                    if p.get('id') == project_id:
                        projects[i] = {**project, 'id': project_id}
                        break
            else:
                project_id = str(uuid.uuid4())
                project['id'] = project_id
                projects.append(project)
            write_json(PROJECTS_FILE, projects)
    except Exception as e:
        print(f'[Project save error] {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

    return jsonify({
        'success': True,
        'project_id': project_id or project.get('id', ''),
        'message': 'Project saved!'
    })

@app.route('/api/projects', methods=['GET'])
def list_projects():
    """List all saved projects"""
    uid = get_user_id()
    try:
        if supabase:
            result = supabase.table('projects').select('id,name,total_cost,budget,created_at,updated_at').eq('user_id', uid).order('updated_at', desc=True).limit(20).execute()
            return jsonify({'success': True, 'projects': result.data})
        else:
            projects = read_json(PROJECTS_FILE)
            return jsonify({'success': True, 'projects': [{
                'id': p.get('id'), 'name': p.get('name'),
                'total_cost': p.get('total_cost', 0),
                'budget': p.get('budget', 100000),
                'created_at': p.get('created_at'),
                'updated_at': p.get('updated_at')
            } for p in projects]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/projects/<project_id>', methods=['GET'])
def load_project(project_id):
    """Load a single project with all items"""
    try:
        if supabase:
            result = supabase.table('projects').select('*').eq('id', project_id).execute()
            if result.data:
                return jsonify({'success': True, 'project': result.data[0]})
        else:
            projects = read_json(PROJECTS_FILE)
            for p in projects:
                if p.get('id') == project_id:
                    return jsonify({'success': True, 'project': p})
        return jsonify({'success': False, 'error': 'Project not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a project"""
    try:
        if supabase:
            supabase.table('projects').delete().eq('id', project_id).execute()
        else:
            projects = read_json(PROJECTS_FILE)
            projects = [p for p in projects if p.get('id') != project_id]
            write_json(PROJECTS_FILE, projects)
        return jsonify({'success': True, 'message': 'Deleted'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ─── START ───
if __name__ == '__main__':
    # Create tables in Supabase if they don't exist (first run)
    if supabase:
        try:
            # Create projects table via raw SQL (Supabase auto-creates if using dashboard)
            supabase.table('projects').select('id').limit(1).execute()
        except:
            print('[instaBuild] Projects table not found — create it in Supabase dashboard:')
            print('  CREATE TABLE projects (id uuid DEFAULT gen_random_uuid() PRIMARY KEY, user_id text, name text, items jsonb, total_cost int, budget int, created_at text, updated_at text);')
        try:
            supabase.table('submissions').select('id').limit(1).execute()
        except:
            print('  CREATE TABLE submissions (id bigserial PRIMARY KEY, name text, email text, phone text, project_type text, message text, timestamp text);')

    app.run(host='0.0.0.0', port=8080, debug=False)
