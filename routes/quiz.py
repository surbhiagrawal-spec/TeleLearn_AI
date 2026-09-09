from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from routes.auth import login_required
from config import TELECOM_TOPICS
from services.quiz_service import (
    parse_quiz_response, create_quiz_attempt, get_quiz_questions,
    submit_quiz, get_quiz_history, get_quiz_stats
)
from services.groq_service import generate_quiz

quiz_bp = Blueprint('quiz', __name__)

@quiz_bp.route('/quiz')
@login_required
def index():
    user_id = session['user_id']
    history = get_quiz_history(user_id, limit=10)
    stats = get_quiz_stats(user_id)
    topic_list = list(TELECOM_TOPICS.keys())
    return render_template('quiz.html', topics=topic_list, history=history, stats=stats)

@quiz_bp.route('/quiz/generate', methods=['POST'])
@login_required
def generate():
    user_id = session['user_id']
    data = request.get_json()
    topic = data.get('topic', '').strip()
    difficulty = data.get('difficulty', 'medium').strip().lower()
    num_questions = int(data.get('num_questions', 5))

    if not topic:
        return jsonify({'error': 'Please select a topic.'}), 400
    if difficulty not in ('easy', 'medium', 'hard'):
        difficulty = 'medium'
    num_questions = max(3, min(num_questions, 15))

    raw, error = generate_quiz(topic, difficulty, num_questions)
    if error:
        return jsonify({'error': error}), 500

    questions, parse_error = parse_quiz_response(raw)
    if parse_error:
        return jsonify({'error': parse_error}), 500

    attempt_id, db_error = create_quiz_attempt(user_id, topic, difficulty, questions)
    if db_error:
        return jsonify({'error': db_error}), 500

    return jsonify({'attempt_id': attempt_id, 'questions': questions, 'topic': topic, 'difficulty': difficulty})

@quiz_bp.route('/quiz/attempt/<int:attempt_id>')
@login_required
def take_quiz(attempt_id):
    user_id = session['user_id']
    from database.db_init import get_db_connection
    conn = get_db_connection()
    try:
        attempt = conn.execute(
            "SELECT * FROM quiz_attempts WHERE id = ? AND user_id = ?", (attempt_id, user_id)
        ).fetchone()
        if not attempt:
            return redirect(url_for('quiz.index'))
    finally:
        conn.close()

    questions = get_quiz_questions(attempt_id)
    return render_template('quiz_take.html', attempt=dict(attempt), questions=questions)

@quiz_bp.route('/quiz/submit/<int:attempt_id>', methods=['POST'])
@login_required
def submit(attempt_id):
    user_id = session['user_id']
    answers = request.get_json()
    if not answers:
        return jsonify({'error': 'No answers provided.'}), 400

    result, error = submit_quiz(attempt_id, user_id, answers)
    if error:
        return jsonify({'error': error}), 500
    return jsonify(result)

@quiz_bp.route('/quiz/results/<int:attempt_id>')
@login_required
def results(attempt_id):
    user_id = session['user_id']
    from database.db_init import get_db_connection
    conn = get_db_connection()
    try:
        attempt = conn.execute(
            "SELECT * FROM quiz_attempts WHERE id = ? AND user_id = ?", (attempt_id, user_id)
        ).fetchone()
        if not attempt:
            return redirect(url_for('quiz.index'))
        questions = conn.execute(
            "SELECT * FROM quiz_questions WHERE attempt_id = ?", (attempt_id,)
        ).fetchall()
    finally:
        conn.close()

    from services.quiz_service import _generate_feedback
    feedback = _generate_feedback(attempt['score_percent'])
    return render_template('results.html',
        attempt=dict(attempt),
        questions=[dict(q) for q in questions],
        feedback=feedback
    )
