import streamlit as st

from analytics.performance import learner_summary
from database.repositories.assessment_repository import AssessmentRepository
from database.repositories.learning_repository import LearningRepository
from utils.auth import require_authenticated_user

st.title("Learner Dashboard")

st.caption("Track your competency development and learning progress.")


# Authentication and database connection
db, user = require_authenticated_user(allowed_roles=["learner"])


# Retrieve learner information
attempts = AssessmentRepository(db).history(user["id"])

learning_repository = LearningRepository(db)

progress = learning_repository.progress_for_user(user["id"])

summary = learner_summary(attempts, progress)


# Welcome section
st.subheader(f"Welcome, {user['name']}!")

st.write(
    "Here is an overview of your competency assessments "
    "and personalized learning activities."
)


# Dashboard metrics
st.divider()

st.subheader("Your Performance Overview")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Assessment Attempts", summary["attempt_count"])

with col2:
    average = summary["average_score"]

    st.metric(
        "Average Assessment Score",
        f"{average}%" if average is not None else "Not assessed",
    )

with col3:
    st.metric("Learning Completion", f"{summary['completion_rate']}%")


# Learning progress
st.divider()

st.subheader("Learning Progress")

st.progress(summary["completion_rate"] / 100)

st.caption(
    f"You have completed {summary['completion_rate']}% "
    "of your recorded learning activities."
)


# Recent assessment history
st.divider()

st.subheader("Recent Assessment History")

if attempts:
    history = []

    for attempt in attempts:
        history.append(
            {
                "Date": attempt.get("created_at"),
                "Career": attempt.get("career_code", "Not specified"),
                "Score": (
                    f"{attempt['overall_score']}%"
                    if attempt.get("overall_score") is not None
                    else "Not scored"
                ),
                "Questions Attempted": attempt.get("total_attempted", 0),
            }
        )

    st.dataframe(history, width="stretch", hide_index=True)

else:
    st.info(
        "You have not completed an assessment yet. "
        "Visit the Assessment page to get started."
    )


# Learning activity summary
st.divider()

st.subheader("Learning Activity Summary")

if progress:
    completed = sum(1 for item in progress if item.get("completed", False))

    pending = len(progress) - completed

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Completed Activities", completed)

    with col2:
        st.metric("Pending Activities", pending)

else:
    st.info(
        "No learning progress has been recorded yet. "
        "Generate a learning roadmap to begin."
    )
