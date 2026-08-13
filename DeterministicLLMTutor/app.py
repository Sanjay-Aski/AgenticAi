"""Streamlit UI for deterministic tutoring agent."""

from __future__ import annotations

import streamlit as st

from config import DB_PATH, TEMPLATES_PATH
from logger import InteractionLogger
from tutor_agent import DeterministicTutorAgent, TutorRequest

st.set_page_config(page_title="Deterministic Tutor", page_icon="🎓", layout="centered")
st.title("Deterministic Tutor - Gov Scheme Assistant")
st.caption("Keyword-based, deterministic, and guardrail-focused tutoring assistant")

if "agent" not in st.session_state:
    logger = InteractionLogger(DB_PATH)
    st.session_state.agent = DeterministicTutorAgent(TEMPLATES_PATH, logger)
    st.session_state.logger = logger

question = st.text_input("Ask your question (example: farmer scheme)")

if st.button("Submit", type="primary"):
    response = st.session_state.agent.answer(TutorRequest(question=question))
    st.subheader("Response")
    st.write(response.response_text)

    with st.expander("Debug Info"):
        st.write(
            {
                "intent": response.intent,
                "version": response.version,
                "guardrail_triggered": response.guardrail_triggered,
                "response_time_ms": response.response_time_ms,
            }
        )

st.subheader("Interaction History")
history = st.session_state.logger.fetch_recent(limit=15)
if history:
    st.dataframe(history, use_container_width=True)
else:
    st.info("No interactions yet.")
