from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from routes.auth import login_required
from services.document_service import save_document, get_user_documents, delete_document, search_documents
from services.rag_service import get_knowledge_base_stats

materials_bp = Blueprint('materials', __name__)

@materials_bp.route('/materials')
@login_required
def index():
    user_id = session['user_id']
    query = request.args.get('q', '').strip()
    if query:
        docs = search_documents(user_id, query)
    else:
        docs = get_user_documents(user_id)
    stats = get_knowledge_base_stats(user_id)
    return render_template('materials.html', documents=docs, stats=stats, query=query)

@materials_bp.route('/materials/upload', methods=['POST'])
@login_required
def upload():
    user_id = session['user_id']
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request.'}), 400

    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected.'}), 400

    doc_id, error = save_document(user_id, file, file.filename)
    if error:
        return jsonify({'error': error}), 400

    from database.db_init import get_db_connection
    conn = get_db_connection()
    try:
        doc = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        doc_dict = dict(doc) if doc else {}
    finally:
        conn.close()

    return jsonify({'success': True, 'document': doc_dict})

@materials_bp.route('/materials/delete/<int:doc_id>', methods=['POST'])
@login_required
def delete(doc_id):
    user_id = session['user_id']
    success, error = delete_document(doc_id, user_id)
    if not success:
        return jsonify({'error': error}), 400
    return jsonify({'success': True})

@materials_bp.route('/materials/stats')
@login_required
def stats():
    user_id = session['user_id']
    return jsonify(get_knowledge_base_stats(user_id))
