from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database.db_init import get_db_connection
import re

auth_bp = Blueprint('auth', __name__)

def is_logged_in():
    return 'user_id' in session

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_logged_in():
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if is_logged_in():
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        full_name = request.form.get('full_name', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        learning_level = request.form.get('learning_level', 'beginner')

        errors = []
        if not username or len(username) < 3:
            errors.append("Username must be at least 3 characters.")
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            errors.append("Username can only contain letters, numbers, and underscores.")
        if not email or not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            errors.append("Please enter a valid email address.")
        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm_password:
            errors.append("Passwords do not match.")

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('register.html', username=username, email=email, full_name=full_name)

        conn = get_db_connection()
        try:
            existing = conn.execute(
                "SELECT id FROM users WHERE username = ? OR email = ?", (username, email)
            ).fetchone()
            if existing:
                flash("Username or email already exists. Please choose another.", 'danger')
                return render_template('register.html', username=username, email=email, full_name=full_name)

            password_hash = generate_password_hash(password)
            conn.execute(
                "INSERT INTO users (username, email, password_hash, full_name, learning_level) VALUES (?,?,?,?,?)",
                (username, email, password_hash, full_name, learning_level)
            )
            conn.commit()
            flash("Registration successful! Please log in.", 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash(f"Registration failed: {str(e)}", 'danger')
        finally:
            conn.close()

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash("Please enter both username and password.", 'danger')
            return render_template('login.html', username=username)

        conn = get_db_connection()
        try:
            user = conn.execute(
                "SELECT * FROM users WHERE username = ? OR email = ?", (username, username.lower())
            ).fetchone()

            if not user or not check_password_hash(user['password_hash'], password):
                flash("Invalid username or password. Please try again.", 'danger')
                return render_template('login.html', username=username)

            conn.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user['id'],))
            conn.commit()

            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name'] or user['username']
            session['learning_level'] = user['learning_level']
            session.permanent = True

            flash(f"Welcome back, {session['full_name']}!", 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        finally:
            conn.close()

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.", 'info')
    return redirect(url_for('main.index'))
