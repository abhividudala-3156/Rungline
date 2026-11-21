import streamlit as st

from database.repositories.user_repository import UserRepository
from services.career_service import CareerService
from utils.auth import require_authenticated_user

st.title("Career Goals")

st.caption(
    "Choose your target career and understand the competencies required to achieve it."
)


# Authentication and database connection
db, user = require_authenticated_user(allowed_roles=["learner"])

# Retrieve available careers
service = CareerService(db)
careers = service.list_careers()

# Prepare career options
options = {
    f"{career['title']} — {career['description']}": career["code"] for career in careers
}

labels = list(options.keys())

current = st.session_state.get("career_code")


default_index = next(
    (index for index, label in enumerate(labels) if options[label] == current), 0
)


# Career selection
st.subheader("Select Your Target Career")

with st.form("career_form"):
    selected = st.selectbox("Available career paths", labels, index=default_index)

    submitted = st.form_submit_button("Save Career Goal", width="stretch")


# Save selected career
if submitted:
    code = options[selected]

    repository = UserRepository(db)

    if repository.update_career_goal(user["id"], code):
        st.session_state.career_code = code
        st.success("Your career goal has been saved successfully.")
        st.rerun()
    else:
        st.error("Unable to update your career goal. Please try again.")

# Display current career
selected_career = st.session_state.get("career_code")


if selected_career:
    career_doc = next(
        (career for career in careers if career["code"] == selected_career), None
    )

    if career_doc:
        st.divider()

        st.subheader("Your Current Career Goal")

        st.markdown(f"### {career_doc['title']}")

        st.write(career_doc["description"])

        st.caption(f"Career Code: {career_doc['code']}")

        # Required competencies
        requirements = service.requirements(selected_career)

        st.divider()

        st.subheader("Required Competencies")

        if requirements:
            st.caption(
                f"{len(requirements)} competencies are mapped to your selected career."
            )

            for index, item in enumerate(requirements, start=1):
                competency = item.get("competency", {})

                name = competency.get("name", item["competency_code"])

                with st.container(border=True):
                    st.markdown(f"**{index}. {name}**")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric("Required Level", f"{item['required_level']}/5")

                    with col2:
                        st.metric("Competency Weight", f"{item['weight']}")

        else:
            st.info("No competency requirements are mapped to this career yet.")

else:
    st.info("Select a career goal to view its required competencies.")
