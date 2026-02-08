from rag import rag_answer
from adaptive_questions import generate_followup_questions
import json

USE_ADAPTIVE_QUESTIONS = True


def collect_symptoms():
    print("\n🤖 Carenova Health Assistant")
    print("Hi, I’m here to help you. Let’s talk about how you’re feeling.\n")

    initial_symptoms = input("Describe your symptoms:\n> ")
    answers = [initial_symptoms]

    if USE_ADAPTIVE_QUESTIONS:
        followups = generate_followup_questions(initial_symptoms)

        if not followups:
            followups = [
                "How long have you had these symptoms?",
                "Are the symptoms getting worse?",
                "Anything else unusual you noticed?"
            ]
    else:
        followups = []

    for question in followups:
        answer = input(question + "\n> ")
        answers.append(answer)

    return " | ".join(answers)


def calculate_severity(symptom_text):
    text = symptom_text.lower()

    severe_keywords = [
        "chest pain",
        "shortness of breath",
        "breathing difficulty",
        "confusion",
        "bluish lips",
        "seizure",
        "unconscious",
        "vomiting blood",
        "severe bleeding"
    ]

    moderate_keywords = [
        "high fever",
        "persistent vomiting",
        "severe weakness"
    ]

    if any(k in text for k in severe_keywords):
        return "Severe"

    if any(k in text for k in moderate_keywords):
        return "Moderate"

    return "Mild"


def calculate_confidence(symptom_text, severity):
    score = 65
    text = symptom_text.lower()

    smart_keywords = [
        "thirst", "urination", "fatigue",
        "weight loss", "blurred vision",
        "fever", "cough", "rash",
        "pain", "headache"
    ]

    for k in smart_keywords:
        if k in text:
            score += 4

    if severity == "Severe":
        score += 10

    return min(score, 96)


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

    # Safe fallback
    if (
        not rag_data
        or "possible_conditions" not in rag_data
        or not rag_data["possible_conditions"]
    ):
        rag_data = {
            "possible_conditions": ["Medical evaluation recommended"],
            "explanation": ["Symptoms were not strongly matched."],
            "home_care_tips": ["Rest", "Stay hydrated", "Monitor symptoms"],
            "when_to_see_doctor": ["If symptoms persist or worsen"],
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

    print("\n📋 Carenova's Guidance:\n")
    print(json.dumps(result, indent=4))
