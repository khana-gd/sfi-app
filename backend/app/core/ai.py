import logging
import httpx
from typing import Optional
from app.core.config import settings

logger = logging.getLogger("kanha.ai")

# Distress/emotional crisis keywords for immediate Level 3 escalation
DISTRESS_KEYWORDS = [
    "kill myself", "want to die", "harm myself", "hurt myself", "commit suicide",
    "end my life", "give up on life", "depressed", "mental breakdown",
    "cannot cope", "anxiety attack", "panic attack", "family crisis",
    "family emergency", "hospital", "accident", "emergency admission"
]

class DistressCrisisDetected(Exception):
    """Raised when student message shows signs of personal or emotional crisis."""
    pass

def detect_distress(text: str) -> bool:
    """Scan text for emotional crisis indicators."""
    lower_text = text.lower()
    for kw in DISTRESS_KEYWORDS:
        if kw in lower_text:
            return True
    return False

def detect_distress_semantic(text: str) -> bool:
    """Scan text for emotional crisis indicators using semantic check via Gemini if available,
    falling back to keyword matching.
    """
    # Check keywords first (works offline and as fast fallback)
    if detect_distress(text):
        return True
        
    api_key = settings.GEMINI_API_KEY
    model_name = settings.GEMINI_MODEL or "gemini-3.6-flash"
    if not api_key or api_key == "dummy_gemini_key_for_dev":
        return False  # Purely keyword fallback in dev/offline
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    prompt = (
        "Analyze the following student message and determine if it shows signs of personal/emotional crisis, "
        "self-harm, severe anxiety, panic, depression, or family emergencies unrelated to the assignment. "
        "Answer with exactly 'YES' if a crisis/distress is detected, or 'NO' if it is just a standard academic/grading query.\n\n"
        f"Message: {text}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.post(url, json=payload)
            if response.status_code == 200:
                result = response.json()
                ans = result["candidates"][0]["content"]["parts"][0]["text"].strip().upper()
                if "YES" in ans:
                    return True
    except Exception as e:
        logger.warning(f"Semantic distress check via Gemini failed: {e}")
    return False

# System Prompt matching SFI brand values: Navy (professionalism, depth), Gold (prestige, quality), Pink (creativity, accent)
SFI_MENTOR_PROMPT = """
You are KANHA, the AI Academic Companion for the Studio Fashion Institute (SFI).
Your character traits:
- Tone: Professional, style-conscious, encouraging, mentoring, and constructive.
- Strategy: Never provide a direct copy-paste answer or do the student's work for them. Instead, guide them with design questions, structural hints, pattern placement suggestions, and historical fashion contexts.
- Formatting: Use clear structured Markdown with brief bullet points. Focus on creative design guidelines.
"""

def generate_gemini_response(prompt: str, category: str) -> str:
    """Generate response using direct Google GenAI REST calls or fallback to mock."""
    if detect_distress_semantic(prompt):
        raise DistressCrisisDetected("Emotional/personal crisis detected in prompt.")

    api_key = settings.GEMINI_API_KEY
    model_name = settings.GEMINI_MODEL or "gemini-3.6-flash"

    # Fallback to mock if using dummy credentials
    if not api_key or api_key == "dummy_gemini_key_for_dev":
        return get_mock_response(prompt, category)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": SFI_MENTOR_PROMPT}]}
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                logger.warning(f"Gemini API returned status {response.status_code}: {response.text}")
                return get_mock_response(prompt, category)
    except Exception as e:
        logger.warning(f"Failed to communicate with Gemini REST API: {e}")
        return get_mock_response(prompt, category)

def generate_copilot_draft(student_query: str, category: str) -> str:
    """Generate a draft answer for the faculty to review and edit."""
    api_key = settings.GEMINI_API_KEY
    model_name = settings.GEMINI_MODEL or "gemini-3.6-flash"

    system_instruction = (
        "You are KANHA, drafting a reply for an SFI faculty member. "
        "Create a professional, clear, and comprehensive reply template answering the student's question directly. "
        "Keep it structured and ready for the tutor to edit or send."
    )

    if not api_key or api_key == "dummy_gemini_key_for_dev":
        return f"Draft response: Let's address your query on {category}. Regarding '{student_query}', here are structural suggestions: [Tutor Edit Here]"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": f"Draft a response to this query: {student_query}"}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]}
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                return f"Draft response: Let's address your query on {category}. Regarding '{student_query}', here are structural suggestions: [Tutor Edit Here]"
    except Exception as e:
        logger.warning(f"Failed to generate draft reply: {e}")
        return f"Draft response: Regarding '{student_query}', please review: [Tutor Edit Here]"

def get_mock_response(prompt: str, category: str) -> str:
    """Fallback rich mock responses aligned with SFI branding."""
    if category == "ASSIGNMENT_HELP":
        return (
            "### SFI Design Guidelines\n\n"
            "For your assignment study, I suggest studying Mughal costume geometry:\n"
            "*   **Symmetry**: Look at the balance in layout and borders.\n"
            "*   **Flora and Fauna**: Integrate delicate leaf-and-flower patterns on borders.\n"
            "*   **Fabric selection**: Think about lightweight silks or crisp linen bases.\n\n"
            "Try sketching out the base block before layering motifs. What fabrics were you planning to specify?"
        )
    elif category == "INSTRUCTION_HELP":
        return (
            "### SFI Technical Illustration Tips\n\n"
            "To clarify design sketch lines:\n"
            "*   Use high-contrast pen weights for the outer garment silhouette.\n"
            "*   Keep interior drape fold lines soft and thin.\n"
            "*   Use cross-hatching sparingly to denote depth in fabric folds.\n\n"
            "Let me know which section of the illustration guidelines you'd like to dive into next!"
        )
    else:
        return (
            "### KANHA Companion Guidance\n\n"
            f"Regarding your query on '{category}':\n"
            "1.  Refine your core concept block first.\n"
            "2.  Consult SFI's design directory references.\n"
            "3.  Draft a quick prototype block to verify proportions.\n\n"
            "I'm here to guide your design process—tell me how you'd like to iterate!"
        )
