import streamlit as st

from analytics.visualizations import competency_gap_chart
from services.assessment_service import AssessmentService
from services.career_service import CareerService
from services.gap_analysis_service import GapAnalysisService
from utils.auth import require_authenticated_user

st.title("Competency Gap Analysis")

st.caption("Understand your current skills and identify areas for improvement.")


# Authentication and database connection
db, user = require_authenticated_user(allowed_roles=["learner"])


# Career selection
career = st.session_state.get("career_code")

if not career:
    st.warning("Select a career goal first.")
    st.stop()


# Retrieve assessment results
attempts = AssessmentService(db).history(user["id"])

skill_scores = attempts[0].get("skill_scores", {}) if attempts else {}


# Calculate competency gaps
requirements = CareerService(db).requirements(career)

report = GapAnalysisService().analyze(
    requirements,
    skill_scores,
)


# Summary metrics
st.subheader("Your Competency Overview")

col1, col2, col3 = st.columns(3)

with col1:
    score = report["weighted_score"]

    st.metric(
        "Weighted Competency Score",
        f"{score}%" if score is not None else "Not assessed",
    )

with col2:
    st.metric(
        "Assessed Competencies",
        report["assessed_skills"],
    )

with col3:
    st.metric(
        "Total Required Competencies",
        report["total_skills"],
    )


# Assessment completion progress
st.progress(
    report["assessed_skills"] / report["total_skills"] if report["total_skills"] else 0
)

st.caption(
    f"{report['assessed_skills']} of {report['total_skills']} competencies assessed."
)


# Individual competency details
st.divider()

st.subheader("Individual Competency Analysis")

for skill in report["skills"]:
    with st.container(border=True):
        current = skill["current_level"]
        required = skill["required_level"]
        gap = skill["gap"]

        st.markdown(f"### {skill['name']}")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Current Level",
                f"{current}/5" if current is not None else "Not assessed",
            )

        with col2:
            st.metric(
                "Required Level",
                f"{required}/5",
            )

        with col3:
            st.metric(
                "Skill Gap",
                str(gap) if gap is not None else "Unknown",
            )

        if current is None:
            st.info("Complete an assessment to measure this competency.")

        else:
            st.progress(current / 5)

            if gap > 0:
                st.warning(f"Improvement needed: {gap} competency level(s).")
            else:
                st.success("You have met the required competency level.")


# Competency comparison chart
st.divider()

st.subheader("Visual Competency Comparison")

chart = competency_gap_chart(report["skills"])

if chart:
    st.plotly_chart(
        chart,
        width="stretch",
    )
else:
    st.info("Complete an assessment to generate the competency chart.")


# Preserve report for other pages
st.session_state.latest_gap_report = report
