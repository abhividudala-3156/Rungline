import streamlit as st

from agents.orchestrator import LearningOrchestrator
from database.connection import get_database, ping_database
from database.repositories.learning_repository import LearningRepository
from services.assessment_service import AssessmentService
from services.career_service import CareerService
from services.gap_analysis_service import GapAnalysisService
from services.learning_service import LearningService
from utils.auth import require_authenticated_user
from utils.ui_helpers import render_learning_activities, render_resource_links

st.title("Personalized Learning Roadmap")

st.caption("Follow your AI-generated learning plan and track your progress.")


# Authentication and database connection
db, user = require_authenticated_user(allowed_roles=["learner"])

career = st.session_state.get("career_code")

if not career:
    st.warning("Choose a career goal first.")
    st.stop()

# Career selection
career = st.session_state.get("career_code")

if not career:
    st.warning("Choose a career goal first.")
    st.stop()


# Database connection
if not ping_database():
    st.error("MongoDB is unavailable.")
    st.stop()


db = get_database()

career_service = CareerService(db)
assessment_service = AssessmentService(db)
learning_service = LearningService(db)
learning_repository = LearningRepository(db)


# Get career and assessment information
career_doc = career_service.repo.get_career(career)

requirements = career_service.requirements(career)

attempts = assessment_service.history(user["id"])

scores = attempts[0].get("skill_scores", {}) if attempts else {}

report = GapAnalysisService().analyze(requirements, scores)

resources = career_service.repo.get_resources(
    [item["competency_code"] for item in requirements]
)


# Generate roadmap
st.subheader("Generate Your Learning Plan")

st.write(
    "Generate a personalized roadmap based on your "
    "assessment results and competency gaps."
)

if st.button("Generate AI Learning Roadmap", width="stretch"):
    try:
        with st.spinner("Generating your personalized roadmap..."):
            orchestrator = LearningOrchestrator(db)

            path = orchestrator.generate_learning_path(
                user["id"], career, career_doc["title"], report, resources
            )

            learning_service.save_path(user["id"], career, path)

        st.success("Your learning roadmap has been generated!")

        st.rerun()

    except Exception as exc:
        st.error(f"Could not generate roadmap: {exc}")


# Retrieve latest saved roadmap
path_doc = learning_service.latest_path(user["id"])


if not path_doc:
    st.info("No learning roadmap found. Generate your first roadmap above.")

    st.stop()


path_data = path_doc.get("path", {})

steps = path_data.get("steps", [])


# Roadmap summary
st.divider()

st.subheader("Your Personalized Learning Plan")

st.info(path_data.get("summary", "Your personalized competency development plan."))


if not steps:
    st.warning("The saved roadmap does not contain any learning steps.")
    st.stop()


# Load saved progress from MongoDB
progress_records = learning_repository.progress_for_user(user["id"])

progress_map = {
    record["resource_id"]: record.get("completed", False) for record in progress_records
}


# Calculate overall progress
completed_count = 0

for index, step in enumerate(steps, start=1):
    resource_id = f"{path_doc['_id']}:{index}"

    if progress_map.get(resource_id, False):
        completed_count += 1


total_steps = len(steps)

completion_rate = (completed_count / total_steps) * 100


# Progress overview
st.subheader("Learning Progress")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Learning Steps", total_steps)

with col2:
    st.metric("Completed Steps", completed_count)

with col3:
    st.metric("Completion Rate", f"{completion_rate:.0f}%")


st.progress(completion_rate / 100)


# Individual learning steps
st.divider()

st.subheader("Your Learning Activities")


for index, step in enumerate(steps, start=1):
    resource_id = f"{path_doc['_id']}:{index}"

    saved_completed = progress_map.get(resource_id, False)

    with st.container(border=True):
        st.markdown(f"### Step {index}: {step['title']}")

        st.write(step.get("objective", "No objective provided."))

        col1, col2 = st.columns(2)

        with col1:
            st.caption(f"Estimated Time: {step.get('estimated_hours', 0)} hours")

        with col2:
            st.caption(f"Priority: {step.get('priority', 'Not specified')}/10")

        st.markdown("**Activities**")

        render_learning_activities(step.get("activities", []))

        render_resource_links(step.get("resource_urls", []))

        st.divider()

        completed = st.checkbox(
            "Mark this learning step as completed",
            value=saved_completed,
            key=f"completed_{resource_id}",
        )

        if st.button("Save Progress", key=f"save_{resource_id}"):
            try:
                learning_service.set_progress(user["id"], resource_id, completed)

                st.success("Your learning progress has been saved.")

                st.rerun()

            except Exception as exc:
                st.error(f"Could not save progress: {exc}")
