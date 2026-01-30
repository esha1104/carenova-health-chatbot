from rag import rag_answer
from llm import llm
import json

# 🔁 Toggle this to False to go back to fixed questions
USE_ADAPTIVE_QUESTIONS = True

FIXED_QUESTIONS = [
    "Do you have a fever?",
    "Are you experiencing cough, cold, or sore throat?",
    "Do you have body pain or headache?",
    "Have you felt nausea, vomiting, or loose motions?",
    "Are you having any breathing difficulty?",
    "Have you travelled recently?"
]


def generate_followup_questions(symptom_text):
    """
    Uses LLM to generate adaptive follow-up questions
    """
    prompt = f"""
You are a healthcare assistant.

User described symptoms:
{symptom_text}

Task:
- Identify the symptom category
- Ask ONLY 3 relevant follow-up questions
- Questions must be short and yes/no or simple
- Do NOT repeat generic questions unnecessarily
- Do NOT give medical advice

Return ONLY the questions, one per line.
"""

    try:
        response = llm.invoke(prompt)
        questions = [
            line.strip("- ").strip()
            for line in response.split("\n")
            if line.strip()
        ]
        return questions[:3]
    except Exception:
        return []


def collect_symptoms():
    print("\n🤖 Carenova Health Assistant")
    print("Hi, I’m here to help you. Let’s talk about how you’re feeling.\n")

    initial_symptoms = input("Describe your symptoms:\n> ")
    answers = [f"Initial symptoms: {initial_symptoms}"]

    if USE_ADAPTIVE_QUESTIONS:
        followups = generate_followup_questions(initial_symptoms)

        # fallback to fixed questions if LLM fails
        if not followups:
            followups = FIXED_QUESTIONS
    else:
        followups = FIXED_QUESTIONS

    for question in followups:
        answer = input(question + "\n> ")
        answers.append(f"{question} Answer: {answer}")

    return "\n".join(answers)


def calculate_severity(symptom_text):
    symptom_text = symptom_text.lower()

    if "breathing difficulty" in symptom_text or "shortness of breath" in symptom_text:
        return "🔴 Severe"
    if "chest pain" in symptom_text:
        return "🔴 Severe"
    if "high fever" in symptom_text:
        return "🟡 Moderate"
    if "vomiting" in symptom_text or "loose motions" in symptom_text:
        return "🟡 Moderate"

    return "🟢 Mild"


def calculate_confidence(symptom_text, severity):
    score = 60

    if "fever" in symptom_text.lower():
        score += 10
    if "cough" in symptom_text.lower():
        score += 10
    if "breathing difficulty" in symptom_text.lower():
        score += 10
    if severity == "🔴 Severe":
        score += 10

    return min(score, 95)


def normalize_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [value]
    return []


def analyze(symptom_text):
    print("\n🧠 Analyzing your symptoms...\n")

    severity = calculate_severity(symptom_text)
    confidence = calculate_confidence(symptom_text, severity)

    rag_data = rag_answer(symptom_text)

    # 🔹 SAFETY FALLBACK
    if not rag_data.get("possible_conditions"):
        rag_data = {
            "possible_conditions": ["Common viral infection"],
            "explanation": ["Symptoms suggest a mild viral illness"],
            "home_care_tips": ["Rest", "Hydration", "Monitor symptoms"],
            "when_to_see_doctor": ["If symptoms worsen or persist"],
            "disclaimer": "This is not a medical diagnosis."
        }

    return {
        "severity": severity,
        "confidence": f"{confidence}%",
        "possible_conditions": normalize_list(rag_data.get("possible_conditions")),
        "explanation": normalize_list(rag_data.get("explanation")),
        "home_care_tips": normalize_list(rag_data.get("home_care_tips")),
        "when_to_see_doctor": normalize_list(rag_data.get("when_to_see_doctor")),
        "disclaimer": rag_data.get(
            "disclaimer",
            "This is not a medical diagnosis."
        )
    }


if __name__ == "__main__":
    symptoms = collect_symptoms()
    result = analyze(symptoms)

    print("\n📋 Carenova's Guidance (JSON Output):\n")
    print(json.dumps(result, indent=4))
