
import streamlit as st

from services.assessment_service import AssessmentService
from services.progress_service import ProgressService
from utils.auth import require_authenticated_user
from utils.ui_helpers import render_competency_scores

st.title("Competency Assessment")


# Authentication and database connection
db, user = require_authenticated_user(
    allowed_roles=["learner"]
)


# Career selection
career = st.session_state.get("career_code")

if not career:
    st.warning("Choose a career goal first.")
    st.stop()


# Assessment service
service = AssessmentService(db)
questions = service.questions(career)

if not questions:
    st.warning("No questions found for this career.")
    st.stop()


# Assessment instructions
st.markdown(
    "Answer the questions below to evaluate your current competency levels."
)

st.caption("Unanswered questions are excluded from the assessment score.")


# Assessment form
with st.form("assessment_form"):
    answers = {}

    for i, question in enumerate(questions):
        st.markdown(f"### Question {i + 1}")

        choice = st.radio(
            question["prompt"],
            question["options"],
            index=None,
            key=f"ans_{question['code']}",
        )

        if choice is not None:
            answers[question["code"]] = question["options"].index(choice)

        st.divider()

    submitted = st.form_submit_button(
        "Submit Assessment",
        width="stretch",
    )


# Assessment submission
if submitted:
    if not answers:
        st.warning("Please answer at least one question.")

    else:
        try:
            result = service.submit(
                user["id"],
                career,
                answers,
            )

            ProgressService(db).notify(
                user["id"],
                "Your assessment has been submitted.",
                "success",
            )

            st.session_state.last_assessment = result

            st.success("Your assessment was submitted successfully!")

            overall_score = result.get("overall_score")

            st.subheader("Assessment Results")

            if overall_score is not None:
                st.metric(
                    "Overall Assessment Score",
                    f"{overall_score}%",
                )
            else:
                st.info(
                    "Not enough evidence to calculate an overall score."
                )

            render_competency_scores(
                result.get("skill_scores", {}),
                title="Your Competency Performance",
            )

        except Exception as exc:
            st.error(f"Assessment submission failed: {exc}")


# Display the most recently submitted assessment after page reruns
previous_result = st.session_state.get("last_assessment")

if previous_result and not submitted:
    st.divider()

    st.subheader("Previous Assessment Results")

    if previous_result.get("overall_score") is not None:
        st.metric(
            "Overall Score",
            f"{previous_result['overall_score']}%",
        )

    render_competency_scores(
        previous_result.get("skill_scores", {})
    )
