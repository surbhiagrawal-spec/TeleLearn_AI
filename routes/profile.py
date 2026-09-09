from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from routes.auth import login_required
from database.db_init import get_db_connection
from services.quiz_service import get_quiz_stats

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile')
@login_required
def index():
    user_id = session['user_id']
    conn = get_db_connection()
    try:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        quiz_stats = get_quiz_stats(user_id)
        doc_count = conn.execute(
            "SELECT COUNT(*) as n FROM documents WHERE user_id = ?", (user_id,)
        ).fetchone()['n']
        msg_count = conn.execute(
            """SELECT COUNT(*) as n FROM messages m
               JOIN conversations c ON m.conversation_id = c.id
               WHERE c.user_id = ? AND m.role='user'""", (user_id,)
        ).fetchone()['n']
    finally:
        conn.close()
    return render_template('profile.html', user=dict(user), quiz_stats=quiz_stats,
                           doc_count=doc_count, msg_count=msg_count)

@profile_bp.route('/profile/update', methods=['POST'])
@login_required
def update():
    user_id = session['user_id']
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip().lower()
    learning_level = request.form.get('learning_level', 'intermediate')
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')

    conn = get_db_connection()
    try:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

        if not full_name:
            flash("Full name cannot be empty.", 'danger')
            return redirect(url_for('profile.index'))

        import re
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            flash("Invalid email address.", 'danger')
            return redirect(url_for('profile.index'))

        # Check if email taken by another user
        existing = conn.execute(
            "SELECT id FROM users WHERE email = ? AND id != ?", (email, user_id)
        ).fetchone()
        if existing:
            flash("Email already in use by another account.", 'danger')
            return redirect(url_for('profile.index'))

        if new_password:
            if not current_password or not check_password_hash(user['password_hash'], current_password):
                flash("Current password is incorrect.", 'danger')
                return redirect(url_for('profile.index'))
            if len(new_password) < 6:
                flash("New password must be at least 6 characters.", 'danger')
                return redirect(url_for('profile.index'))
            new_hash = generate_password_hash(new_password)
            conn.execute(
                "UPDATE users SET full_name=?, email=?, learning_level=?, password_hash=? WHERE id=?",
                (full_name, email, learning_level, new_hash, user_id)
            )
        else:
            conn.execute(
                "UPDATE users SET full_name=?, email=?, learning_level=? WHERE id=?",
                (full_name, email, learning_level, user_id)
            )

        conn.commit()
        session['full_name'] = full_name
        session['learning_level'] = learning_level
        flash("Profile updated successfully!", 'success')
    except Exception as e:
        flash(f"Update failed: {str(e)}", 'danger')
    finally:
        conn.close()

    return redirect(url_for('profile.index'))

@profile_bp.route('/history')
@login_required
def history():
    user_id = session['user_id']
    conn = get_db_connection()
    try:
        convs = conn.execute(
            "SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,)
        ).fetchall()
        conv_list = []
        for c in convs:
            d = dict(c)
            msg_count = conn.execute(
                "SELECT COUNT(*) as n FROM messages WHERE conversation_id = ?", (c['id'],)
            ).fetchone()['n']
            d['message_count'] = msg_count
            conv_list.append(d)
    finally:
        conn.close()
    return render_template('history.html', conversations=conv_list)

@profile_bp.route('/progress')
@login_required
def progress():
    user_id = session['user_id']
    conn = get_db_connection()
    try:
        import json
        # All quiz attempts
        quiz_attempts = conn.execute(
            "SELECT * FROM quiz_attempts WHERE user_id = ? ORDER BY completed_at DESC",
            (user_id,)
        ).fetchall()

        # Topics studied with counts
        topic_activity = conn.execute(
            """SELECT topic, COUNT(*) as cnt, MAX(created_at) as last_seen
               FROM learning_progress WHERE user_id = ?
               GROUP BY topic ORDER BY cnt DESC""",
            (user_id,)
        ).fetchall()

        # Daily activity (last 30 days)
        daily_activity = conn.execute(
            """SELECT DATE(created_at) as day, COUNT(*) as cnt
               FROM learning_progress WHERE user_id = ?
               AND created_at >= DATE('now', '-30 days')
               GROUP BY day ORDER BY day""",
            (user_id,)
        ).fetchall()

        quiz_stats = get_quiz_stats(user_id)
    finally:
        conn.close()

    # Chart data
    days = [r['day'] for r in daily_activity]
    day_counts = [r['cnt'] for r in daily_activity]
    q_topics = [r['topic'][:15] for r in list(quiz_attempts)[:10]][::-1]
    q_scores = [r['score_percent'] for r in list(quiz_attempts)[:10]][::-1]

    return render_template('progress.html',
        quiz_attempts=[dict(a) for a in quiz_attempts],
        topic_activity=[dict(t) for t in topic_activity],
        quiz_stats=quiz_stats,
        days=json.dumps(days),
        day_counts=json.dumps(day_counts),
        q_topics=json.dumps(q_topics),
        q_scores=json.dumps(q_scores)
    )
