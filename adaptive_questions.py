from llm import llm

def generate_followup_questions(symptom_text):
    prompt = f"""
You are a healthcare assistant.

Based on the following user symptoms:
{symptom_text}

Task:
- Identify the symptom category (respiratory, digestive, skin, neurological, general)
- Ask ONLY 3 relevant follow-up questions
- Questions should be short and simple
- Do NOT give medical advice
- Do NOT repeat questions about fever, cough, travel unless relevant

Return ONLY the questions as a numbered list.
"""

    response = llm.invoke(prompt)

    questions = []
    for line in response.split("\n"):
        if line.strip().startswith(("1", "2", "3")):
            questions.append(line.split(".", 1)[-1].strip())

    return questions[:3]
