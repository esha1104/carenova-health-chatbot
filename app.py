import streamlit as st
from chatbot import analyze
from adaptive_questions import generate_followup_questions

st.set_page_config(page_title="Carenova Health Assistant", page_icon="🤖")
st.title("🤖 Carenova AI Health Assistant")
st.write("Tell me how you're feeling, and I’ll guide you step by step.")

# -------------------------------
# SESSION STATE INITIALIZATION
# -------------------------------
if "stage" not in st.session_state:
    st.session_state.stage = "initial"
    st.session_state.symptom_text = ""
    st.session_state.followup_questions = []
    st.session_state.answers = []
    st.session_state.current_q = 0
    st.session_state.result = None


# -------------------------------
# STAGE 1: INITIAL SYMPTOMS
# -------------------------------
if st.session_state.stage == "initial":
    user_input = st.text_input(
        "What symptoms are you experiencing?",
        placeholder="e.g. urinating often, thirsty, tired"
    )

    if st.button("Next ➡️") and user_input.strip():
        st.session_state.symptom_text = f"Initial symptoms: {user_input}"

        # Generate adaptive questions
        questions = generate_followup_questions(user_input)

        # Safe fallback
        if not questions:
            questions = [
                "How long have you had these symptoms?",
                "Are the symptoms getting worse?",
                "Anything else unusual you noticed?"
            ]

        st.session_state.followup_questions = questions
        st.session_state.stage = "followup"
        st.rerun()


# -------------------------------
# STAGE 2: ADAPTIVE FOLLOW-UP
# -------------------------------
elif st.session_state.stage == "followup":
    q_index = st.session_state.current_q
    question = st.session_state.followup_questions[q_index]

    st.markdown(f"**{question}**")
    answer = st.text_input("Your answer", key=f"answer_{q_index}")

    if st.button("Next ➡️"):
        if answer.strip():
            st.session_state.answers.append(
                f"{question} Answer: {answer}"
            )
            st.session_state.current_q += 1

            if st.session_state.current_q >= len(st.session_state.followup_questions):
                st.session_state.stage = "analyze"

            st.rerun()


# -------------------------------
# STAGE 3: ANALYSIS
# -------------------------------
elif st.session_state.stage == "analyze":
    with st.spinner("🧠 Analyzing your symptoms..."):
        full_text = st.session_state.symptom_text + "\n"
        full_text += "\n".join(st.session_state.answers)

        st.session_state.result = analyze(full_text)

    st.session_state.stage = "result"
    st.rerun()


# -------------------------------
# STAGE 4: RESULT DISPLAY
# -------------------------------
elif st.session_state.stage == "result":
    result = st.session_state.result

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

    if st.button("🔄 Start New Assessment"):
        st.session_state.clear()
        st.rerun()
