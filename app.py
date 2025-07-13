import streamlit as st
from main import InterviewAgent

# ────────────────────────────────────────────────────────────────────────────────
# Page configuration
# ────────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Interview Chat ✨",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ────────────────────────────────────────────────────────────────────────────────
# Load custom CSS
# ────────────────────────────────────────────────────────────────────────────────

def load_css(path: str):
    with open(path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("styles.css")

# ────────────────────────────────────────────────────────────────────────────────
# Session‑state & UI helpers
# ────────────────────────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []  # list[dict]

if "interview_agent" not in st.session_state:
    st.session_state.interview_agent = InterviewAgent()

if "interview_started" not in st.session_state:
    st.session_state.interview_started = False

st.markdown("## 💼 **Interview Chat**")

def display_message(message: dict):
    """Render a chat bubble based on role."""
    bubble_class = "user" if message["role"] == "user" else "assistant"
    st.markdown(
        f'<div class="chat-bubble {bubble_class}">{message["content"]}</div>',
        unsafe_allow_html=True,
    )

# Start interview if not already started
if not st.session_state.interview_started:
    with st.spinner("Starting interview..."):
        # Get the first question from the interview agent
        first_question = st.session_state.interview_agent.get_response([])
        st.session_state.messages.append({"role": "assistant", "content": first_question})
        st.session_state.interview_started = True

# Render chat history
for msg in st.session_state.messages:
    display_message(msg)

# ────────────────────────────────────────────────────────────────────────────────
# Chat input ↔ LLM
# ────────────────────────────────────────────────────────────────────────────────
user_prompt = st.chat_input("Type your response and press Enter…")

if user_prompt:
    # Add user message & show instantly
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    display_message(st.session_state.messages[-1])

    with st.spinner("Interviewer is thinking…"):
        # Get response from interview agent
        assistant_reply = st.session_state.interview_agent.get_response(st.session_state.messages[:])

    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
    display_message(st.session_state.messages[-1])

    # Auto‑scroll to newest message
    st.markdown("""<script>window.scrollTo(0, document.body.scrollHeight);</script>""", unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────────────────────
# Sidebar
# ────────────────────────────────────────────────────────────────────────────────
with st.sidebar.expander("⚙️ Settings & Info", expanded=False):
    st.markdown(
        """
        **Interview Agent**: This is an AI-powered interview simulation.

        **API Key**: Set the `OPENAI_API_KEY` environment variable.

        **Model**: Uses `gpt-4o-mini` for generating follow-up questions.

        **Flow**: 
        - 5 prepared questions
        - Up to 3 follow-up questions based on your responses
        - Intelligent conversation flow

        **Reset**: Refresh the page to restart the interview.
        """
    )

    if st.button("🔄 Reset Interview"):
        st.session_state.messages = []
        st.session_state.interview_agent = InterviewAgent()
        st.session_state.interview_started = False
        st.rerun()
