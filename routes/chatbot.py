from flask import Blueprint, render_template, request, jsonify, session
from routes.auth import login_required
from database.db_init import get_db_connection
from services.groq_service import get_general_answer, get_rag_answer
from services.rag_service import retrieve_relevant_chunks

chatbot_bp = Blueprint('chatbot', __name__)

def _get_or_create_conversation(user_id, conv_id=None):
    conn = get_db_connection()
    try:
        if conv_id:
            conv = conn.execute(
                "SELECT * FROM conversations WHERE id = ? AND user_id = ?", (conv_id, user_id)
            ).fetchone()
            if conv:
                return conv['id']
        cursor = conn.execute(
            "INSERT INTO conversations (user_id, title) VALUES (?, ?)",
            (user_id, 'New Conversation')
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def _save_message(conv_id, role, content, sources=None):
    import json
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO messages (conversation_id, role, content, sources) VALUES (?,?,?,?)",
            (conv_id, role, content, json.dumps(sources) if sources else None)
        )
        conn.execute(
            "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (conv_id,)
        )
        conn.commit()
    finally:
        conn.close()

def _auto_title(conn, conv_id, question):
    current = conn.execute("SELECT title FROM conversations WHERE id = ?", (conv_id,)).fetchone()
    if current and current['title'] == 'New Conversation':
        title = question[:60] + ('…' if len(question) > 60 else '')
        conn.execute("UPDATE conversations SET title = ? WHERE id = ?", (title, conv_id))
        conn.commit()

@chatbot_bp.route('/chatbot')
@login_required
def index():
    user_id = session['user_id']
    conn = get_db_connection()
    try:
        convs = conn.execute(
            "SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC LIMIT 20",
            (user_id,)
        ).fetchall()
    finally:
        conn.close()
    return render_template('chatbot.html', conversations=[dict(c) for c in convs])

@chatbot_bp.route('/chatbot/send', methods=['POST'])
@login_required
def send_message():
    import json
    user_id = session['user_id']
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    question = data.get('message', '').strip()
    conv_id = data.get('conversation_id')
    use_rag = data.get('use_rag', True)
    level = session.get('learning_level', 'intermediate')

    if not question:
        return jsonify({'error': 'Message cannot be empty.'}), 400
    if len(question) > 2000:
        return jsonify({'error': 'Message too long (max 2000 characters).'}), 400

    conv_id = _get_or_create_conversation(user_id, conv_id)
    _save_message(conv_id, 'user', question)

    # Auto-set conversation title from first question
    conn = get_db_connection()
    try:
        _auto_title(conn, conv_id, question)
        history = conn.execute(
            "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY created_at ASC LIMIT 10",
            (conv_id,)
        ).fetchall()
    finally:
        conn.close()

    history_list = [{'role': r['role'], 'content': r['content']} for r in history]

    sources_used = []
    answer = None
    error = None

    if use_rag:
        chunks = retrieve_relevant_chunks(question, user_id, top_k=4)
        if chunks:
            answer, error = get_rag_answer(question, chunks, level=level)
            sources_used = [{'source': c['source'], 'chunk': c['chunk_index'], 'score': round(c['score'], 3)} for c in chunks]
        else:
            answer, error = get_general_answer(question, conversation_history=history_list[:-1], level=level)
    else:
        answer, error = get_general_answer(question, conversation_history=history_list[:-1], level=level)

    if error:
        return jsonify({'error': error, 'conversation_id': conv_id}), 500

    _save_message(conv_id, 'assistant', answer, sources=sources_used if sources_used else None)

    # Record learning progress
    conn = get_db_connection()
    try:
        import re
        topic = 'General'
        telecom_keywords = ['5g', '4g', 'lte', 'gsm', 'cdma', 'ofdm', 'mimo', 'wifi', 'fiber',
                            'antenna', 'signal', 'modulation', 'protocol', 'tcp', 'routing',
                            'satellite', 'iot', 'spectrum', 'bandwidth', 'frequency']
        q_lower = question.lower()
        for kw in telecom_keywords:
            if kw in q_lower:
                topic = kw.upper()
                break
        conn.execute(
            "INSERT INTO learning_progress (user_id, topic, activity_type, details) VALUES (?,?,?,?)",
            (user_id, topic, 'chat', question[:200])
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify({
        'answer': answer,
        'conversation_id': conv_id,
        'sources': sources_used
    })

@chatbot_bp.route('/chatbot/conversation/<int:conv_id>')
@login_required
def get_conversation(conv_id):
    import json
    user_id = session['user_id']
    conn = get_db_connection()
    try:
        conv = conn.execute(
            "SELECT * FROM conversations WHERE id = ? AND user_id = ?", (conv_id, user_id)
        ).fetchone()
        if not conv:
            return jsonify({'error': 'Conversation not found.'}), 404

        messages = conn.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
            (conv_id,)
        ).fetchall()

        msgs_list = []
        for m in messages:
            d = dict(m)
            if d.get('sources'):
                try:
                    d['sources'] = json.loads(d['sources'])
                except Exception:
                    d['sources'] = []
            msgs_list.append(d)

        return jsonify({'conversation': dict(conv), 'messages': msgs_list})
    finally:
        conn.close()

@chatbot_bp.route('/chatbot/conversation/<int:conv_id>/delete', methods=['POST'])
@login_required
def delete_conversation(conv_id):
    user_id = session['user_id']
    conn = get_db_connection()
    try:
        conn.execute(
            "DELETE FROM conversations WHERE id = ? AND user_id = ?", (conv_id, user_id)
        )
        conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()

@chatbot_bp.route('/chatbot/new', methods=['POST'])
@login_required
def new_conversation():
    user_id = session['user_id']
    conv_id = _get_or_create_conversation(user_id)
    return jsonify({'conversation_id': conv_id})
