from rag import rag_answer
from adaptive_questions import generate_followup_questions
import json


USE_ADAPTIVE_QUESTIONS = True


def collect_symptoms():
    print("\n🤖 Carenova Health Assistant")
    print("Hi, I’m here to help you. Let’s talk about how you’re feeling.\n")

    # Step 1: Free-text symptoms
    initial_symptoms = input("Describe your symptoms:\n> ")
    answers = [f"Initial symptoms: {initial_symptoms}"]

    # Step 2: Adaptive follow-ups
    if USE_ADAPTIVE_QUESTIONS:
        followups = generate_followup_questions(initial_symptoms)

        # Safe fallback if LLM fails
        if not followups:
            followups = [
                "How long have you had these symptoms?",
                "Are the symptoms getting worse?",
                "Anything else unusual you noticed?"
            ]
    else:
        followups = []

    # Step 3: Ask follow-up questions
    for question in followups:
        answer = input(question + "\n> ")
        answers.append(f"{question} Answer: {answer}")

    return "\n".join(answers)


def calculate_severity(symptom_text):
    text = symptom_text.lower()

    if any(k in text for k in ["breathing difficulty", "shortness of breath", "chest pain"]):
        return "🔴 Severe"
    if any(k in text for k in ["vomiting", "loose motions", "high fever"]):
        return "🟡 Moderate"

    return "🟢 Mild"


def calculate_confidence(symptom_text, severity):
    score = 60
    text = symptom_text.lower()

    for k in ["fever", "cough", "tired", "weak", "thirst", "urinate", "hunger", "weight"]:
        if k in text:
            score += 5

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

    # 🔒 SMART, SYMPTOM-AWARE FALLBACK
    text = symptom_text.lower()

    METABOLIC_KEYWORDS = [
        "urinate", "thirst", "tired", "fatigue",
        "hunger", "appetite", "weight"
    ]

    if not rag_data.get("possible_conditions"):
        if any(k in text for k in METABOLIC_KEYWORDS):
            rag_data = {
                "possible_conditions": [
                    "Metabolic condition (possible blood sugar imbalance)"
                ],
                "explanation": [
                    "Frequent urination, increased thirst, fatigue, and appetite or weight changes may be associated with blood sugar regulation issues"
                ],
                "home_care_tips": [
                    "Maintain hydration",
                    "Avoid excessive sugary foods",
                    "Follow a balanced diet",
                    "Monitor symptoms"
                ],
                "when_to_see_doctor": [
                    "If symptoms persist beyond a few days",
                    "For blood sugar testing or medical evaluation"
                ],
                "disclaimer": "This is not a medical diagnosis."
            }
        else:
            rag_data = {
                "possible_conditions": ["General health condition"],
                "explanation": [
                    "Based on the symptoms, a specific condition could not be confidently identified"
                ],
                "home_care_tips": [
                    "Rest",
                    "Stay hydrated",
                    "Monitor symptoms closely"
                ],
                "when_to_see_doctor": [
                    "If symptoms persist or worsen"
                ],
                "disclaimer": "This is not a medical diagnosis."
            }

    return {
        "severity": severity,
        "confidence": f"{confidence}%",
        "possible_conditions": normalize_list(rag_data.get("possible_conditions")),
        "explanation": normalize_list(rag_data.get("explanation")),
        "home_care_tips": normalize_list(rag_data.get("home_care_tips")),
        "when_to_see_doctor": normalize_list(rag_data.get("when_to_see_doctor")),
        "disclaimer": rag_data.get("disclaimer")
    }


if __name__ == "__main__":
    symptoms = collect_symptoms()
    result = analyze(symptoms)

    print("\n📋 Carenova's Guidance (JSON Output):\n")
    print(json.dumps(result, indent=4))
