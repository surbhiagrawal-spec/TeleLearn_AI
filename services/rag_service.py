import os
import sys
import re
import math
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from database.db_init import get_db_connection

# ─── simple TF-IDF without sklearn dependency ────────────────────────────────

def _tokenize(text):
    """Lowercase, strip punctuation, split on whitespace."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return [t for t in text.split() if len(t) > 2]

def _tf(tokens):
    counts = Counter(tokens)
    total = len(tokens) if tokens else 1
    return {word: count / total for word, count in counts.items()}

def _idf(word, doc_token_lists):
    n_docs = len(doc_token_lists) or 1
    n_with = sum(1 for tokens in doc_token_lists if word in set(tokens)) or 1
    return math.log(n_docs / n_with)

def _tfidf_vector(tokens, doc_token_lists):
    tf = _tf(tokens)
    return {word: score * _idf(word, doc_token_lists) for word, score in tf.items()}

def _cosine_similarity(vec_a, vec_b):
    common = set(vec_a) & set(vec_b)
    if not common:
        return 0.0
    dot = sum(vec_a[w] * vec_b[w] for w in common)
    mag_a = math.sqrt(sum(v ** 2 for v in vec_a.values())) or 1
    mag_b = math.sqrt(sum(v ** 2 for v in vec_b.values())) or 1
    return dot / (mag_a * mag_b)

# ─── chunk helpers ────────────────────────────────────────────────────────────

def chunk_text(text, chunk_size=None, overlap=None):
    """Split text into overlapping word-count chunks."""
    chunk_size = chunk_size or Config.CHUNK_SIZE
    overlap = overlap or Config.CHUNK_OVERLAP

    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i: i + chunk_size]
        chunk = ' '.join(chunk_words)
        if chunk.strip():
            chunks.append(chunk)
        i += chunk_size - overlap
        if i >= len(words):
            break
    return chunks

# ─── database-backed retrieval ────────────────────────────────────────────────

def store_chunks(document_id, chunks):
    """Persist text chunks for a document."""
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM document_chunks WHERE document_id = ?", (document_id,))
        for idx, chunk in enumerate(chunks):
            conn.execute(
                "INSERT INTO document_chunks (document_id, chunk_index, content, word_count) VALUES (?,?,?,?)",
                (document_id, idx, chunk, len(chunk.split()))
            )
        conn.execute(
            "UPDATE documents SET chunk_count = ? WHERE id = ?",
            (len(chunks), document_id)
        )
        conn.commit()
    finally:
        conn.close()

def retrieve_relevant_chunks(query, user_id, top_k=None):
    """
    Retrieve the most relevant chunks from the user's uploaded documents
    using a pure-Python TF-IDF / cosine-similarity approach.
    Returns a list of dicts with keys: content, source, chunk_index, score.
    """
    top_k = top_k or Config.MAX_RETRIEVAL_CHUNKS
    conn = get_db_connection()
    try:
        rows = conn.execute(
            """SELECT dc.id, dc.content, dc.chunk_index, d.original_name
               FROM document_chunks dc
               JOIN documents d ON dc.document_id = d.id
               WHERE d.user_id = ?
               ORDER BY d.uploaded_at DESC""",
            (user_id,)
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        return []

    # Build token lists for all chunks
    all_tokens = [_tokenize(row['content']) for row in rows]
    query_tokens = _tokenize(query)

    # Score each chunk
    query_vec = _tfidf_vector(query_tokens, all_tokens)
    scored = []
    for i, (row, tokens) in enumerate(zip(rows, all_tokens)):
        chunk_vec = _tfidf_vector(tokens, all_tokens)
        score = _cosine_similarity(query_vec, chunk_vec)
        scored.append({
            'content': row['content'],
            'source': row['original_name'],
            'chunk_index': row['chunk_index'],
            'score': score
        })

    # Return top-k by score, minimum threshold 0.05
    scored.sort(key=lambda x: x['score'], reverse=True)
    results = [c for c in scored[:top_k] if c['score'] > 0.05]
    return results

def get_knowledge_base_stats(user_id):
    """Return summary counts for a user's knowledge base."""
    conn = get_db_connection()
    try:
        doc_count = conn.execute(
            "SELECT COUNT(*) as n FROM documents WHERE user_id = ?", (user_id,)
        ).fetchone()['n']
        chunk_count = conn.execute(
            """SELECT COUNT(*) as n FROM document_chunks dc
               JOIN documents d ON dc.document_id = d.id WHERE d.user_id = ?""",
            (user_id,)
        ).fetchone()['n']
        return {'documents': doc_count, 'chunks': chunk_count}
    finally:
        conn.close()
