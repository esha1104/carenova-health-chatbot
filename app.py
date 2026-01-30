import streamlit as st
from chatbot import analyze

st.set_page_config(page_title="Carenova Health Assistant", page_icon="🤖")

st.title("🤖 Carenova AI Health Assistant")
st.write("Answer the questions below to get health guidance.")


# QUESTIONS
QUESTIONS = [
    "What symptoms are you experiencing?",
    "Do you have a fever?",
    "Do you have cough, cold, or sore throat?",
    "Do you have body pain or headache?",
    "Any nausea, vomiting, or loose motions?",
    "Any breathing difficulty?",
    "Recent travel history?"
]


# Initialize session state
if "responses" not in st.session_state:
    print("session not created")
    st.session_state.responses = {}

# Form for inputs (STABLE)
with st.form("health_form"):
    for q in QUESTIONS:
        st.session_state.responses[q] = st.text_input(q)

    submitted = st.form_submit_button("🧠 Analyze Symptoms")

# On submit
if submitted:
    with st.spinner("Analyzing your symptoms..."):
        symptom_text = ""
        for q, a in st.session_state.responses.items():
            symptom_text += f"{q} Answer: {a}\n"

        result = analyze(symptom_text)

    st.success("Analysis Complete ✅")

    st.subheader("📋 Carenova's Guidance")

    st.markdown(f"### Severity: {result['severity']}")
    st.markdown(f"### Confidence: {result['confidence']}")

    st.markdown("### Possible Conditions")
    for c in result["possible_conditions"]:
        st.write(f"- {c}")

    st.markdown("### Explanation")
    for e in result["explanation"]:
        st.write(f"- {e}")

    st.markdown("### Home Care Tips")
    for tip in result["home_care_tips"]:
        st.write(f"- {tip}")

    st.markdown("### When to See a Doctor")
    for w in result["when_to_see_doctor"]:
        st.write(f"- {w}")

    st.caption(result["disclaimer"])
