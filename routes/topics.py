from flask import Blueprint, render_template, request, jsonify, session
from routes.auth import login_required
from config import TELECOM_TOPICS
from services.groq_service import get_topic_overview, get_telecom_explanation
from database.db_init import get_db_connection

topics_bp = Blueprint('topics', __name__)

@topics_bp.route('/topics')
@login_required
def index():
    return render_template('topics.html', topics=TELECOM_TOPICS)

@topics_bp.route('/topics/<topic_name>')
@login_required
def topic_detail(topic_name):
    topic_data = TELECOM_TOPICS.get(topic_name)
    if not topic_data:
        # Try case-insensitive match
        for key in TELECOM_TOPICS:
            if key.lower() == topic_name.lower():
                topic_name = key
                topic_data = TELECOM_TOPICS[key]
                break
    if not topic_data:
        return render_template('topics.html', topics=TELECOM_TOPICS, error=f"Topic '{topic_name}' not found.")

    # Record visit
    user_id = session['user_id']
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO learning_progress (user_id, topic, activity_type, details) VALUES (?,?,?,?)",
            (user_id, topic_name, 'topic_view', topic_name)
        )
        conn.commit()
    finally:
        conn.close()

    return render_template('topic_detail.html', topic_name=topic_name, topic_data=topic_data)

@topics_bp.route('/topics/api/overview', methods=['POST'])
@login_required
def get_overview():
    data = request.get_json()
    topic_name = data.get('topic', '').strip()
    if not topic_name:
        return jsonify({'error': 'Topic name required.'}), 400

    answer, error = get_topic_overview(topic_name)
    if error:
        return jsonify({'error': error}), 500
    return jsonify({'overview': answer})

@topics_bp.route('/topics/api/explain', methods=['POST'])
@login_required
def explain_concept():
    data = request.get_json()
    concept = data.get('concept', '').strip()
    level = data.get('level', session.get('learning_level', 'intermediate'))
    mode = data.get('mode', 'explain')

    if not concept:
        return jsonify({'error': 'Concept is required.'}), 400

    # Record activity
    user_id = session['user_id']
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO learning_progress (user_id, topic, activity_type, details) VALUES (?,?,?,?)",
            (user_id, concept[:100], 'explain', f"{mode}:{level}")
        )
        conn.commit()
    finally:
        conn.close()

    answer, error = get_telecom_explanation(concept, level=level, mode=mode)
    if error:
        return jsonify({'error': error}), 500
    return jsonify({'explanation': answer, 'concept': concept, 'level': level, 'mode': mode})
