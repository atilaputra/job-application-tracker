import pymysql
import pymysql.cursors
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime
import os
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# MySQL Configuration
MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
MYSQL_DB = os.environ.get('MYSQL_DB', 'job_tracker_db')

# Function to get database connection
def get_db_connection():
    # Check if running on Azure (has MYSQL_HOST env var)
    if 'MYSQL_HOST' in os.environ and 'azure' in os.environ.get('MYSQL_HOST', ''):
        # Azure MySQL - use SSL
        connection = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            ssl={'ssl': True},
            cursorclass=pymysql.cursors.Cursor
        )
    else:
        # Local MySQL - no SSL
        connection = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            cursorclass=pymysql.cursors.Cursor
        )
    return connection

# File upload configuration
UPLOAD_FOLDER = 'uploads/resumes'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Home page - Dashboard
@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get all applications
    cur.execute("SELECT * FROM applications ORDER BY date_applied DESC")
    applications = cur.fetchall()
    
    # Get statistics
    cur.execute("SELECT COUNT(*) FROM applications")
    total_apps = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM applications WHERE status = 'Applied'")
    applied = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM applications WHERE status = 'Interview'")
    interviews = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM applications WHERE status = 'Offer'")
    offers = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM applications WHERE status = 'Rejected'")
    rejected = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    stats = {
        'total': total_apps,
        'applied': applied,
        'interviews': interviews,
        'offers': offers,
        'rejected': rejected
    }
    
    return render_template('index.html', applications=applications, stats=stats)

# Add new application
@app.route('/add', methods=['GET', 'POST'])
def add_application():
    if request.method == 'POST':
        company = request.form['company']
        role = request.form['role']
        job_link = request.form['job_link']
        status = request.form['status']
        notes = request.form['notes']
        date_applied = request.form['date_applied']
        
        # Handle resume upload
        resume_path = None
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to avoid conflicts
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                resume_path = filename
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO applications 
            (company, role, job_link, status, notes, date_applied, resume_path) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (company, role, job_link, status, notes, date_applied, resume_path))
        conn.commit()
        cur.close()
        conn.close()
        
        flash('Application added successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('add.html')

# Edit application
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_application(id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        company = request.form['company']
        role = request.form['role']
        job_link = request.form['job_link']
        status = request.form['status']
        notes = request.form['notes']
        date_applied = request.form['date_applied']
        
        # Handle resume upload
        resume_path = request.form.get('current_resume')
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                resume_path = filename
        
        cur.execute("""
            UPDATE applications 
            SET company=%s, role=%s, job_link=%s, status=%s, notes=%s, 
                date_applied=%s, resume_path=%s, updated_at=NOW()
            WHERE id=%s
        """, (company, role, job_link, status, notes, date_applied, resume_path, id))
        conn.commit()
        cur.close()
        conn.close()
        
        flash('Application updated successfully!', 'success')
        return redirect(url_for('index'))
    
    cur.execute("SELECT * FROM applications WHERE id = %s", [id])
    application = cur.fetchone()
    cur.close()
    conn.close()
    
    return render_template('edit.html', application=application)

# Delete application
@app.route('/delete/<int:id>')
def delete_application(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM applications WHERE id = %s", [id])
    conn.commit()
    cur.close()
    conn.close()
    
    flash('Application deleted successfully!', 'success')
    return redirect(url_for('index'))

# API endpoint for statistics (for future use)
@app.route('/api/stats')
def get_stats():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT status, COUNT(*) as count FROM applications GROUP BY status")
    results = cur.fetchall()
    cur.close()
    conn.close()
    
    stats = {row[0]: row[1] for row in results}
    return jsonify(stats)

# View/Download resume
@app.route('/resume/<filename>')
def view_resume(filename):
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
