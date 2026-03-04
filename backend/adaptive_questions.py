from llm import llm


def generate_followup_questions(symptom_text):
    """
    Generate intelligent follow-up questions
    to improve medical differentiation.
    """

    prompt = f"""
You are a cautious healthcare assistant.

User symptoms:
{symptom_text}

Generate EXACTLY 3 follow-up questions.

Rules:
- Questions must help differentiate illnesses
- Keep each question under 12 words
- No diagnosis
- No advice
- No explanations
- Avoid repeating symptoms

Return ONLY the questions.
"""

    try:
        response = llm.invoke(prompt)

        questions = []

        for line in response.split("\n"):

            line = line.strip()

            # Remove numbering like 1. 2) -
            line = line.lstrip("0123456789.-) ")

            if "?" not in line:
                continue

            questions.append(line)

        # Safety fallback (VERY IMPORTANT)
        if len(questions) < 3:
            return [
                "How long have you had these symptoms?",
                "Are the symptoms worsening?",
                "Do you have fever or pain?"
            ]

        return questions[:3]

    except Exception:

        # Hard fallback — bot never breaks
        return [
            "How long have you had these symptoms?",
            "Are the symptoms getting worse?",
            "Have you noticed anything unusual (pain, fever, fatigue)?"
        ]
