import streamlit as st

from database.connection import ping_database
from database.repositories.user_repository import UserRepository
from utils.auth import require_authenticated_user

st.title("My Profile")

st.caption("View your account information and registration details.")


# Authentication and database connection
db, user = require_authenticated_user(
    allowed_roles=["learner"]
)


# Database connection
if not ping_database():
    st.error("MongoDB is unavailable.")
    st.stop()


# Retrieve user information
repository = UserRepository(db)

record = repository.by_id(user["id"])

# Profile overview
st.subheader("Account Overview")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Full Name**")

    st.write(record.get("name", "Not available"))


with col2:
    st.markdown("**Account Role**")

    role = record.get("role", "learner")

    st.write(role.replace("_", " ").title())


st.divider()


# Personal information
st.subheader("Personal Information")

st.text_input("Full Name", value=record.get("name", ""), disabled=True)

st.text_input("Email Address", value=record.get("email", ""), disabled=True)


# Account information
st.divider()

st.subheader("Account Information")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Account Status**")

    if record.get("is_active", False):
        st.success("Active")

    else:
        st.warning("Inactive")


with col2:
    st.markdown("**User Role**")

    st.info(role.replace("_", " ").title())


st.caption(
    "Your account identity information is currently read-only. "
    "Profile editing can be added in a future version."
)
