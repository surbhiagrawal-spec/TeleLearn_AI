import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

def get_groq_client():
    if not GROQ_AVAILABLE:
        return None, "Groq library not installed. Run: pip install groq"
    if not Config.GROQ_API_KEY or Config.GROQ_API_KEY.strip() in ('', 'your_groq_api_key_here'):
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        return None, (
            f"GROQ_API_KEY not set. "
            f"Please add your API key to: {env_path}\n"
            f"Format: GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx"
        )
    try:
        client = Groq(api_key=Config.GROQ_API_KEY)
        return client, None
    except Exception as e:
        return None, f"Failed to initialize Groq client: {str(e)}"

def chat_with_groq(messages, system_prompt=None, temperature=0.7, max_tokens=2048):
    client, error = get_groq_client()
    if error:
        return None, error

    formatted_messages = []
    if system_prompt:
        formatted_messages.append({"role": "system", "content": system_prompt})
    formatted_messages.extend(messages)

    try:
        response = client.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=formatted_messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        content = response.choices[0].message.content
        if not content or not content.strip():
            return None, "Received an empty response from the AI. Please try again."
        return content.strip(), None
    except Exception as e:
        err_str = str(e).lower()
        if 'api key' in err_str or 'authentication' in err_str or '401' in err_str:
            return None, "Invalid API key. Please check your GROQ_API_KEY in the .env file."
        elif 'rate limit' in err_str or '429' in err_str:
            return None, "Rate limit reached. Please wait a moment and try again."
        elif 'timeout' in err_str:
            return None, "Request timed out. Please try again."
        elif 'model' in err_str:
            return None, f"Model error: {str(e)}. Try changing GROQ_MODEL in config."
        else:
            return None, f"AI service error: {str(e)}"

def get_telecom_explanation(concept, level='beginner', mode='explain'):
    level_instructions = {
        'beginner': "Use simple language, avoid jargon, use analogies from everyday life.",
        'intermediate': "Use technical terms with brief explanations, include formulas where relevant.",
        'advanced': "Use full technical depth, mathematical notation, industry standards references."
    }

    mode_prompts = {
        'explain': f"Explain the telecom concept clearly for a {level} learner.",
        'example': f"Explain with a concrete, practical example for a {level} learner.",
        'step_by_step': f"Explain step-by-step how it works for a {level} learner.",
        'technical': "Give a deep technical explanation with formulas, standards, and implementation details.",
        'compare': f"Compare and contrast the two concepts clearly for a {level} learner."
    }

    system_prompt = f"""You are TeleLearn AI, an expert telecom engineering tutor.
{level_instructions.get(level, level_instructions['beginner'])}
{mode_prompts.get(mode, mode_prompts['explain'])}

Structure your response as follows:
**Simple Explanation:** (2-3 sentences)
**Key Concepts:** (bullet points)
**Example:** (concrete example)
**Real-World Telecom Application:** (how it's used in the industry)
**Important Points to Remember:** (bullet points)
**Follow-up Question:** (suggest one question to deepen understanding)
"""

    messages = [{"role": "user", "content": f"Explain: {concept}"}]
    return chat_with_groq(messages, system_prompt=system_prompt, temperature=0.5)

def get_rag_answer(question, retrieved_chunks, level='intermediate'):
    level_instructions = {
        'beginner': "Use simple language and analogies.",
        'intermediate': "Balance technical accuracy with clarity.",
        'advanced': "Use full technical depth and formulas."
    }

    context = "\n\n---\n\n".join([
        f"[Source: {c.get('source', 'Document')} | Chunk {c.get('chunk_index', '')}]\n{c.get('content', '')}"
        for c in retrieved_chunks
    ])

    system_prompt = f"""You are TeleLearn AI, an expert telecom engineering tutor.
Answer questions PRIMARILY based on the provided learning materials context below.
{level_instructions.get(level, level_instructions['intermediate'])}

CONTEXT FROM LEARNING MATERIALS:
{context}

INSTRUCTIONS:
1. Base your answer primarily on the provided context.
2. If the context is sufficient, start with "📚 Based on the learning materials:"
3. If the context is partial, use it and supplement with your knowledge, clearly labeling which is which.
4. If the context is not relevant, state: "ℹ️ The uploaded materials don't cover this topic directly."
5. Always structure: Explanation → Key Points → Example (if applicable).
6. Be accurate and educational.
"""

    messages = [{"role": "user", "content": question}]
    return chat_with_groq(messages, system_prompt=system_prompt, temperature=0.4)

def get_general_answer(question, conversation_history=None, level='intermediate'):
    level_instructions = {
        'beginner': "Use simple language, avoid jargon, use analogies.",
        'intermediate': "Balance technical accuracy with clarity.",
        'advanced': "Use full technical depth and formulas."
    }

    system_prompt = f"""You are TeleLearn AI, an intelligent telecom learning assistant.
You help students and engineers learn wireless communication, networking, protocols, signal processing and telecom concepts.
{level_instructions.get(level, level_instructions['intermediate'])}

For every response:
**Simple Explanation:** Brief, clear answer.
**Key Concepts:** Bullet points of important ideas.
**Example:** Practical example.
**Real-World Application:** How it's used in telecom industry.
**Important Points:** Key takeaways.
**Suggested Follow-up:** One question to explore next.

If asked something non-telecom related, politely redirect to telecom topics.
"""

    messages = []
    if conversation_history:
        for msg in conversation_history[-6:]:
            messages.append({"role": msg['role'], "content": msg['content']})
    messages.append({"role": "user", "content": question})

    return chat_with_groq(messages, system_prompt=system_prompt, temperature=0.6)

def generate_quiz(topic, difficulty, num_questions):
    difficulty_instructions = {
        'easy': "basic recall and understanding questions suitable for beginners",
        'medium': "application and analysis questions for intermediate learners",
        'hard': "complex synthesis and evaluation questions for advanced learners"
    }

    system_prompt = f"""You are TeleLearn AI quiz generator for telecom engineering students.
Generate exactly {num_questions} multiple choice questions about "{topic}" at {difficulty} difficulty.
These should be {difficulty_instructions.get(difficulty, difficulty_instructions['medium'])}.

Return ONLY a valid JSON array, no extra text, no markdown fences. Format:
[
  {{
    "question": "Question text here?",
    "option_a": "First option",
    "option_b": "Second option",
    "option_c": "Third option",
    "option_d": "Fourth option",
    "correct": "A",
    "explanation": "Explanation of why this is correct and others are wrong."
  }}
]

Rules:
- correct must be exactly "A", "B", "C", or "D"
- All options must be distinct and plausible
- Explanations must be educational
- Questions must be technically accurate
- No duplicate questions
"""

    messages = [{"role": "user", "content": f"Generate {num_questions} {difficulty} MCQ questions about {topic} in telecom."}]
    return chat_with_groq(messages, system_prompt=system_prompt, temperature=0.7, max_tokens=3000)

def get_topic_overview(topic_name):
    system_prompt = """You are TeleLearn AI, a telecom engineering expert.
Provide a comprehensive topic overview structured as:

**Overview:** (2-3 sentences introduction)
**Core Concepts:**
- List 5-7 key concepts with 1-sentence explanations each
**How It Works:** (3-4 sentence technical explanation)
**Real-World Applications:**
- 3-4 industry applications
**Why It Matters:** (importance in modern telecom)
**Key Standards/Specifications:** (relevant standards like 3GPP, IEEE, ITU)
**Related Topics:** (2-3 connected topics to explore next)
"""

    messages = [{"role": "user", "content": f"Give me a comprehensive overview of {topic_name} in telecommunications."}]
    return chat_with_groq(messages, system_prompt=system_prompt, temperature=0.5)
