from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import date
import re

app = Flask(__name__)
app.secret_key = "secret123"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ===== Database Models =====
class User(db.Model):
    email = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(100))
    password = db.Column(db.String(200))
    role = db.Column(db.String(10))
    mobile = db.Column(db.String(10))

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100))
    description = db.Column(db.String(300))
    assigned_to = db.Column(db.String(100), db.ForeignKey('user.email'))
    status = db.Column(db.String(20), default='Pending')

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    staff_email = db.Column(db.String(100), db.ForeignKey('user.email'))
    status = db.Column(db.String(10))
    date = db.Column(db.String(10))  # YYYY-MM-DD

# ===== Validation functions =====
def is_valid_email(email):
    return re.match(r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$', email)

def is_valid_mobile(mobile):
    return re.match(r'^[0-9]{10}$', mobile)

# ===== Routes =====
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user'] = user.email
            return redirect(url_for('admin_dashboard') if user.role=='admin' else url_for('staff_dashboard'))
        flash("Invalid Credentials!", "error")
    return render_template("login.html")

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        mobile = request.form['mobile']
        role = request.form['role']

        if not is_valid_email(email):
            flash("Invalid Email Format!", "error")
            return redirect(url_for('register'))
        if not is_valid_mobile(mobile):
            flash("Invalid Mobile Number!", "error")
            return redirect(url_for('register'))
        if User.query.get(email):
            flash("Email already registered!", "error")
            return redirect(url_for('register'))

        new_user = User(
            email=email,
            name=name,
            password=generate_password_hash(password),
            role=role,
            mobile=mobile
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Registration Successful! Please Login.", "success")
        return redirect(url_for('login'))
    return render_template("register.html")

# ===== Forgot Password =====
import secrets
import string
from werkzeug.security import generate_password_hash

# ===== Forgot Password =====
def generate_temp_password(length=10):
    """Generate a unique temporary password with letters, digits, and symbols"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    temp_password = ''.join(secrets.choice(characters) for _ in range(length))
    return temp_password

@app.route('/forgot_password', methods=['GET','POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.get(email)
        if user:
            temp_pass = generate_temp_password()
            user.password = generate_password_hash(temp_pass)
            db.session.commit()
            # Ideally, send temp_pass via email or SMS here
            flash(f"Temporary Password: {temp_pass} (please change after login)", "success")
        else:
            flash("Email not found!", "error")
    return render_template("forgot_password.html")


# ===== Admin Dashboard =====
@app.route('/admin_dashboard', methods=['GET','POST'])
def admin_dashboard():
    user_email = session.get('user')
    if not user_email:
        return redirect(url_for('login'))

    current_user = User.query.get(user_email)
    if current_user.role != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Assign Task
        if 'task_title' in request.form:
            title = request.form['task_title']
            desc = request.form['task_description']
            staff_email = request.form['assigned_to']
            staff_member = User.query.get(staff_email)
            if staff_member and staff_member.role=='staff':
                db.session.add(Task(title=title, description=desc, assigned_to=staff_email))
                db.session.commit()
                flash("Task Assigned Successfully!", "success")
            else:
                flash("Invalid Staff Email!", "error")
        # Mark Attendance
        elif 'attendance_staff' in request.form:
            staff_email = request.form['attendance_staff']
            status = request.form['attendance_status']
            today = str(date.today())
            existing = Attendance.query.filter_by(staff_email=staff_email, date=today).first()
            if not existing:
                db.session.add(Attendance(staff_email=staff_email, status=status, date=today))
                db.session.commit()
                flash("Attendance Marked Successfully!", "success")
            else:
                flash("Attendance already marked for today!", "error")

    staff_list = User.query.filter_by(role='staff').all()
    tasks = Task.query.all()
    attendance = Attendance.query.all()
    return render_template("dashboard_admin.html", user=current_user, staff=staff_list, tasks=tasks, attendance=attendance)

# ===== Staff Dashboard =====
@app.route('/staff_dashboard', methods=['GET','POST'])
def staff_dashboard():
    user_email = session.get('user')
    if not user_email:
        return redirect(url_for('login'))

    current_user = User.query.get(user_email)
    if current_user.role != 'staff':
        return redirect(url_for('login'))

    if request.method == 'POST':
        task_id = int(request.form['task_id'])
        task = Task.query.get(task_id)
        if task and task.assigned_to == user_email:
            task.status = "Completed"
            db.session.commit()
            flash("Task marked as Completed!", "success")

    my_tasks = Task.query.filter_by(assigned_to=user_email).all()
    today = str(date.today())
    staff_attendance = Attendance.query.filter_by(staff_email=user_email, date=today).all()
    return render_template("dashboard_staff.html", user=current_user, tasks=my_tasks, attendance=staff_attendance)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET','POST'])
def profile():
    user_email = session.get('user')
    if not user_email:
        return redirect(url_for('login'))
    current_user = User.query.get(user_email)

    if request.method == 'POST':
        name = request.form['name']
        mobile = request.form['mobile']
        password = request.form['password']

        if not is_valid_mobile(mobile):
            flash("Invalid Mobile Number!", "error")
            return redirect(url_for('profile'))

        current_user.name = name
        current_user.mobile = mobile
        if password:
            current_user.password = generate_password_hash(password)
        db.session.commit()
        flash("Profile Updated Successfully!", "success")

    return render_template("profile.html", user=current_user)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
