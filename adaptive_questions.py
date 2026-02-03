from llm import llm


def generate_followup_questions(symptom_text):
    """
    Generate adaptive follow-up questions using LLM
    based on user's initial symptoms.
    """

    prompt = f"""
You are a healthcare assistant.

User symptoms:
{symptom_text}

Task:
- Identify the symptom category (metabolic, respiratory, digestive, skin, neurological, etc.)
- Ask ONLY 3 relevant follow-up questions
- Questions must be short and simple
- Avoid generic questions like fever/cough unless relevant
- Do NOT give advice or diagnoses

Return ONLY the questions, one per line.
"""

    try:
        response = llm.invoke(prompt)

        questions = []

        for line in response.split("\n"):
            line = line.strip()

            # Remove numbering like "1.", "2)", "-"
            line = line.lstrip("0123456789.-) ")

            # Ignore non-question lines
            if "?" not in line:
                continue

            questions.append(line)

        return questions[:3]

    except Exception:
        return []
