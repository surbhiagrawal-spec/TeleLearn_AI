import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_init import get_db_connection
from services.groq_service import generate_quiz

def parse_quiz_response(raw_text):
    """Parse the raw Groq JSON response into a list of question dicts."""
    if not raw_text:
        return None, "Empty response from AI."
    try:
        text = raw_text.strip()
        # Strip possible markdown code fences
        if text.startswith('```'):
            lines = text.split('\n')
            text = '\n'.join(lines[1:])
            if text.strip().endswith('```'):
                text = '\n'.join(text.strip().split('\n')[:-1])
        # Find the JSON array
        start = text.find('[')
        end = text.rfind(']') + 1
        if start == -1 or end == 0:
            return None, "AI did not return a valid JSON quiz format. Please try again."
        json_str = text[start:end]
        questions = json.loads(json_str)

        # Validate structure
        required_keys = {'question', 'option_a', 'option_b', 'option_c', 'option_d', 'correct', 'explanation'}
        validated = []
        for q in questions:
            if not isinstance(q, dict):
                continue
            if not required_keys.issubset(set(q.keys())):
                continue
            if q.get('correct', '').upper() not in ('A', 'B', 'C', 'D'):
                q['correct'] = 'A'
            else:
                q['correct'] = q['correct'].upper()
            validated.append(q)

        if not validated:
            return None, "No valid questions found in AI response."
        return validated, None
    except json.JSONDecodeError as e:
        return None, f"Failed to parse quiz JSON: {str(e)}"
    except Exception as e:
        return None, f"Quiz parsing error: {str(e)}"

def create_quiz_attempt(user_id, topic, difficulty, questions):
    """Store quiz attempt and questions in the database. Returns attempt_id."""
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO quiz_attempts (user_id, topic, difficulty, total_questions) VALUES (?,?,?,?)",
            (user_id, topic, difficulty, len(questions))
        )
        attempt_id = cursor.lastrowid

        for q in questions:
            conn.execute(
                """INSERT INTO quiz_questions
                   (attempt_id, question_text, option_a, option_b, option_c, option_d, correct_option, explanation)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (attempt_id, q['question'], q['option_a'], q['option_b'],
                 q['option_c'], q['option_d'], q['correct'], q.get('explanation', ''))
            )
        conn.commit()
        return attempt_id, None
    except Exception as e:
        return None, str(e)
    finally:
        conn.close()

def get_quiz_questions(attempt_id):
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM quiz_questions WHERE attempt_id = ? ORDER BY id",
            (attempt_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def submit_quiz(attempt_id, user_id, answers):
    """
    answers: dict {question_id: 'A'|'B'|'C'|'D'}
    Returns result dict.
    """
    conn = get_db_connection()
    try:
        attempt = conn.execute(
            "SELECT * FROM quiz_attempts WHERE id = ? AND user_id = ?",
            (attempt_id, user_id)
        ).fetchone()
        if not attempt:
            return None, "Quiz attempt not found."

        questions = conn.execute(
            "SELECT * FROM quiz_questions WHERE attempt_id = ?", (attempt_id,)
        ).fetchall()

        correct_count = 0
        results = []
        for q in questions:
            qid = str(q['id'])
            user_ans = answers.get(qid, '').upper()
            is_correct = (user_ans == q['correct_option'].upper())
            if is_correct:
                correct_count += 1

            conn.execute(
                "UPDATE quiz_questions SET user_answer = ?, is_correct = ? WHERE id = ?",
                (user_ans, 1 if is_correct else 0, q['id'])
            )
            results.append({
                'id': q['id'],
                'question': q['question_text'],
                'option_a': q['option_a'],
                'option_b': q['option_b'],
                'option_c': q['option_c'],
                'option_d': q['option_d'],
                'correct_option': q['correct_option'],
                'user_answer': user_ans,
                'is_correct': is_correct,
                'explanation': q['explanation']
            })

        score_percent = round((correct_count / len(questions)) * 100, 1) if questions else 0

        conn.execute(
            "UPDATE quiz_attempts SET correct_answers = ?, score_percent = ? WHERE id = ?",
            (correct_count, score_percent, attempt_id)
        )

        # Record learning progress
        conn.execute(
            """INSERT INTO learning_progress (user_id, topic, activity_type, details)
               VALUES (?,?,?,?)""",
            (user_id, attempt['topic'], 'quiz',
             json.dumps({'score': score_percent, 'correct': correct_count, 'total': len(questions)}))
        )
        conn.commit()

        feedback = _generate_feedback(score_percent)
        return {
            'attempt_id': attempt_id,
            'topic': attempt['topic'],
            'difficulty': attempt['difficulty'],
            'total': len(questions),
            'correct': correct_count,
            'score_percent': score_percent,
            'feedback': feedback,
            'results': results
        }, None
    except Exception as e:
        return None, str(e)
    finally:
        conn.close()

def _generate_feedback(score_percent):
    if score_percent >= 90:
        return "🏆 Excellent! You have a strong grasp of this topic!"
    elif score_percent >= 75:
        return "👍 Great job! You understand most of the key concepts."
    elif score_percent >= 60:
        return "📚 Good effort! Review the incorrect answers to strengthen your understanding."
    elif score_percent >= 40:
        return "💡 Keep studying! Focus on the concepts you missed."
    else:
        return "📖 This topic needs more attention. Review the fundamentals and try again."

def get_quiz_history(user_id, limit=20):
    conn = get_db_connection()
    try:
        rows = conn.execute(
            """SELECT * FROM quiz_attempts WHERE user_id = ?
               ORDER BY completed_at DESC LIMIT ?""",
            (user_id, limit)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def get_quiz_stats(user_id):
    conn = get_db_connection()
    try:
        stats = conn.execute(
            """SELECT COUNT(*) as total_quizzes,
                      AVG(score_percent) as avg_score,
                      MAX(score_percent) as best_score,
                      SUM(total_questions) as total_questions_answered
               FROM quiz_attempts WHERE user_id = ?""",
            (user_id,)
        ).fetchone()
        return dict(stats) if stats else {}
    finally:
        conn.close()
