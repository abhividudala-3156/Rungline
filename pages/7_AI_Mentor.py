import streamlit as st

from agents.orchestrator import LearningOrchestrator
from database.connection import get_database, ping_database
from services.assessment_service import AssessmentService
from services.career_service import CareerService
from services.gap_analysis_service import GapAnalysisService
from utils.auth import require_authenticated_user
from utils.ui_helpers import render_recommendations

st.title("AI Learning Mentor")

st.caption("Get personalized learning guidance based on your competency assessment.")

# Authentication and database connection
db, user = require_authenticated_user(
    allowed_roles=["learner"]
)


# Career selection
career = st.session_state.get("career_code")

if not career:
    st.warning("Select a career goal first.")
    st.stop()


# Database connection
if not ping_database():
    st.error("MongoDB is unavailable.")
    st.stop()


db = get_database()


# User question
st.subheader("Ask Your Learning Mentor")

question = st.text_area(
    "What would you like guidance on?",
    placeholder="Example: How can I improve my SQL skills?",
    height=100,
)


if st.button("Get Learning Guidance", disabled=not question.strip(), width="stretch"):
    try:
        with st.spinner("Preparing your personalized guidance..."):
            career_service = CareerService(db)
            assessment_service = AssessmentService(db)

            career_doc = career_service.repo.get_career(career)

            attempts = assessment_service.history(user["id"])

            scores = attempts[0].get("skill_scores", {}) if attempts else {}

            report = GapAnalysisService().analyze(
                career_service.requirements(career), scores
            )

            answer = LearningOrchestrator(db).feedback_for(career_doc["title"], report)

            st.session_state.mentor_answer = answer
            st.session_state.mentor_question = question

    except Exception as exc:
        st.error(f"Unable to generate learning guidance: {exc}")


# Display guidance
answer = st.session_state.get("mentor_answer")

if answer:
    st.divider()

    st.subheader("Your Learning Guidance")

    st.write("Your question:")
    st.text(st.session_state.get("mentor_question", ""))

    render_recommendations(answer.get("summary", ""), answer.get("recommendations", []))


st.divider()

st.caption(
    "Guidance is generated from your latest competency assessment "
    "and selected career goal."
)
