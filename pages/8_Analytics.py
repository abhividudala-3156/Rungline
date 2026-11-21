import pandas as pd
import streamlit as st

from analytics.performance import learner_summary
from analytics.visualizations import progress_chart
from database.connection import get_database, ping_database
from database.repositories.assessment_repository import AssessmentRepository
from database.repositories.learning_repository import LearningRepository
from utils.auth import require_authenticated_user

st.title("Learning Analytics")

st.caption("Monitor your assessment performance and learning development.")


# Authentication and database connection
db, user = require_authenticated_user(
    allowed_roles=["learner"]
)

# Database connection
if not ping_database():
    st.error("MongoDB is unavailable.")
    st.stop()


db = get_database()

assessment_repository = AssessmentRepository(db)
learning_repository = LearningRepository(db)


# Retrieve learner data
attempts = assessment_repository.history(user["id"])

progress = learning_repository.progress_for_user(user["id"])

summary = learner_summary(attempts, progress)


# Calculate learning activity metrics
completed = sum(1 for item in progress if item.get("completed", False))

pending = len(progress) - completed


# Performance overview
st.subheader("Performance Overview")

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


# Learning activity overview
st.divider()

st.subheader("Learning Activity Overview")

col1, col2 = st.columns(2)

with col1:
    st.metric("Completed Activities", completed)

with col2:
    st.metric("Pending Activities", pending)


st.progress(summary["completion_rate"] / 100)

st.caption(f"{summary['completion_rate']}% of recorded learning activities completed.")


# Learning progress visualization
st.divider()

st.subheader("Learning Progress Visualization")

chart = progress_chart(progress)

if chart:
    st.plotly_chart(chart, width="stretch")

else:
    st.info(
        "Your learning progress chart will appear after you start "
        "a personalized learning roadmap."
    )


# Assessment performance trend
st.divider()

st.subheader("Assessment Performance Trend")

if attempts:
    data = [
        {"Attempt": index, "Score": attempt.get("overall_score")}
        for index, attempt in enumerate(reversed(attempts), start=1)
        if attempt.get("overall_score") is not None
    ]

    if data:
        dataframe = pd.DataFrame(data).set_index("Attempt")

        st.line_chart(
            dataframe, y="Score", x_label="Assessment Attempt", y_label="Score (%)"
        )

        st.caption("Track how your assessment scores change across attempts.")

    else:
        st.info("No scored assessment attempts are available yet.")

else:
    st.info("Complete an assessment to start tracking your performance trend.")


# Assessment history
st.divider()

st.subheader("Assessment History")

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
    st.info("No assessment history is available.")
