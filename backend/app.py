import streamlit as st
from adaptive_questions import generate_followup_questions
from chatbot import analyze


# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Carenova AI Health Assistant",
    page_icon="🤖",
    layout="wide"
)

# -------------------------------------------------
# CSS
# -------------------------------------------------
st.markdown("""
<style>
html, body {
    height: 100%;
    margin: 0;
}

.stApp {
    min-height: 100vh;
    background: linear-gradient(
        180deg,
        #f6a5c0 0%,
        #d6b0d8 35%,
        #9fd6cc 100%
    );
}

.block-container {
    max-width: 100% !important;
    padding-top: 1.5rem !important;
}

header, footer {
    visibility: hidden;
}

.chat-row {
    display: flex;
    margin-bottom: 14px;
    padding-left: 12%;
    padding-right: 12%;
}

.chat-row.bot {
    justify-content: flex-start;
}

.chat-row.bot .bubble {
    background: rgba(255, 255, 255, 0.85);
    border-radius: 18px 18px 18px 6px;
    padding: 14px 18px;
    max-width: 60%;
}

.chat-row.user {
    justify-content: flex-end;
}

.chat-row.user .bubble {
    background: #dcf8c6;
    border-radius: 18px 18px 6px 18px;
    padding: 14px 18px;
    max-width: 60%;
}

.bubble {
    font-size: 15px;
    line-height: 1.55;
    color: #000;
}
</style>
""", unsafe_allow_html=True)


# -------------------------------------------------
# MESSAGE RENDER
# -------------------------------------------------
def render_message(role, content):
    side = "user" if role == "user" else "bot"
    st.markdown(
        f"""
        <div class="chat-row {side}">
            <div class="bubble">
                {content}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.stage = "initial"
    st.session_state.symptom_text = ""
    st.session_state.followups = []
    st.session_state.answers = []
    st.session_state.q_index = 0
    st.session_state.analysis_done = False  # ⭐ NEW

    st.session_state.messages.append({
        "role": "assistant",
        "content": (
            "<b>Hi, I’m Carenova</b> 🤍<br><br>"
            "Tell me how you're feeling, and I’ll guide you step by step.<br><br>"
            "<i>Take your time — I’m here with you.</i>"
        )
    })


# -------------------------------------------------
# 🚨 AUTO ANALYSIS (FIXES FREEZE)
# -------------------------------------------------
if st.session_state.stage == "analyze" and not st.session_state.analysis_done:

    with st.spinner("🧠 Analyzing your symptoms..."):

        full_text = (
            st.session_state.symptom_text
            + " | "
            + " | ".join(st.session_state.answers)
        )

        result = analyze(full_text)

    severity = result.get("severity", "unknown")

    bot_reply = (
        f"💙 <b>Here’s what I understand</b><br><br>"
        f"Your symptoms appear <b>{severity.lower()}</b>.<br><br>"

        "<b>🔍 Possible conditions</b><br>"
        f"• {', '.join(result['possible_conditions'])}<br><br>"

        "<b>🏠 What may help</b><br>"
        + "<br>".join("• " + tip for tip in result["home_care_tips"]) + "<br><br>"

        "<b>🚨 See a doctor if</b><br>"
        + "<br>".join("• " + w for w in result["when_to_see_doctor"]) + "<br><br>"

        "<i>⚠️ This is not a medical diagnosis.</i>"
    )

    st.session_state.messages.append({
        "role": "assistant",
        "content": bot_reply
    })

    st.session_state.stage = "done"
    st.session_state.analysis_done = True
    st.rerun()


# -------------------------------------------------
# DISPLAY CHAT
# -------------------------------------------------
for msg in st.session_state.messages:
    render_message(msg["role"], msg["content"])


# -------------------------------------------------
# CHAT INPUT
# -------------------------------------------------
user_input = st.chat_input("Type how you're feeling...")


if user_input:

    # restart support
    if user_input.lower() in ["restart", "start again", "reset"]:
        st.session_state.clear()
        st.rerun()

    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })


    # ---------------- INITIAL ----------------
    if st.session_state.stage == "initial":

        st.session_state.symptom_text = user_input
        st.session_state.followups = generate_followup_questions(user_input)

        if not st.session_state.followups:
            st.session_state.followups = [
                "How long have you had these symptoms?",
                "Are they getting worse?",
                "Anything else unusual?"
            ]

        st.session_state.stage = "followup"
        st.session_state.q_index = 0

        bot_reply = f"Thank you for sharing 🤍<br><br>{st.session_state.followups[0]}"


    # ---------------- FOLLOWUPS ----------------
    elif st.session_state.stage == "followup":

        st.session_state.answers.append(user_input)
        st.session_state.q_index += 1

        if st.session_state.q_index < len(st.session_state.followups):
            bot_reply = st.session_state.followups[st.session_state.q_index]

        else:
            st.session_state.stage = "analyze"
            st.session_state.analysis_done = False  # ⭐ IMPORTANT
            bot_reply = "Got it 💙 Let me analyze everything you shared..."


    # ---------------- DONE ----------------
    else:
        bot_reply = "Type <b>restart</b> whenever you'd like a new assessment 🌱"


    st.session_state.messages.append({
        "role": "assistant",
        "content": bot_reply
    })

    st.rerun()


# -------------------------------------------------
# RESET BUTTON
# -------------------------------------------------
if st.session_state.stage == "done":
    st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
    if st.button("🔄 Start New Assessment"):
        st.session_state.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
