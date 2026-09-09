from flask import Blueprint, render_template, session
from routes.auth import login_required
from database.db_init import get_db_connection
from services.quiz_service import get_quiz_stats
from services.rag_service import get_knowledge_base_stats
import json

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def index():
    user_id = session['user_id']
    conn = get_db_connection()
    try:
        # Messages / questions asked
        questions_asked = conn.execute(
            """SELECT COUNT(*) as n FROM messages m
               JOIN conversations c ON m.conversation_id = c.id
               WHERE c.user_id = ? AND m.role = 'user'""",
            (user_id,)
        ).fetchone()['n']

        # Distinct topics studied
        topics_studied = conn.execute(
            "SELECT COUNT(DISTINCT topic) as n FROM learning_progress WHERE user_id = ?",
            (user_id,)
        ).fetchone()['n']

        # Recent activity (last 8 entries)
        recent_activity = conn.execute(
            """SELECT activity_type, topic, details, created_at
               FROM learning_progress WHERE user_id = ?
               ORDER BY created_at DESC LIMIT 8""",
            (user_id,)
        ).fetchall()

        # Quiz performance over time (last 10 quizzes)
        quiz_history = conn.execute(
            """SELECT topic, score_percent, completed_at
               FROM quiz_attempts WHERE user_id = ?
               ORDER BY completed_at DESC LIMIT 10""",
            (user_id,)
        ).fetchall()

        # Topics breakdown (for chart)
        topic_counts = conn.execute(
            """SELECT topic, COUNT(*) as cnt FROM learning_progress
               WHERE user_id = ? GROUP BY topic ORDER BY cnt DESC LIMIT 8""",
            (user_id,)
        ).fetchall()

        # Conversations
        conv_count = conn.execute(
            "SELECT COUNT(*) as n FROM conversations WHERE user_id = ?", (user_id,)
        ).fetchone()['n']

    finally:
        conn.close()

    quiz_stats = get_quiz_stats(user_id)
    kb_stats = get_knowledge_base_stats(user_id)

    # Prepare chart data
    quiz_labels = [q['topic'][:15] for q in reversed(list(quiz_history))]
    quiz_scores = [q['score_percent'] for q in reversed(list(quiz_history))]
    topic_labels = [t['topic'][:20] for t in topic_counts]
    topic_data = [t['cnt'] for t in topic_counts]

    activity_list = []
    for act in recent_activity:
        details = {}
        try:
            details = json.loads(act['details']) if act['details'] else {}
        except Exception:
            pass
        activity_list.append({
            'type': act['activity_type'],
            'topic': act['topic'],
            'details': details,
            'created_at': act['created_at']
        })

    return render_template('dashboard.html',
        questions_asked=questions_asked,
        topics_studied=topics_studied,
        quiz_stats=quiz_stats,
        kb_stats=kb_stats,
        conv_count=conv_count,
        activity_list=activity_list,
        quiz_labels=json.dumps(quiz_labels),
        quiz_scores=json.dumps(quiz_scores),
        topic_labels=json.dumps(topic_labels),
        topic_data=json.dumps(topic_data)
    )
