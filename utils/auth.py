
from datetime import datetime, timedelta, timezone

import streamlit as st

from config import settings
from database.connection import get_database, ping_database
from database.repositories.user_repository import UserRepository

USER_SESSION_KEYS = {
    "user",
    "authenticated_at",
    "career_code",
    "last_assessment",
    "latest_gap_report",
    "mentor_answer",
    "mentor_question",
}


def clear_user_session():
    """Remove user-specific data while preserving application state."""
    for key in list(st.session_state.keys()):
        if key in USER_SESSION_KEYS or key.startswith("ans_"):
            st.session_state.pop(key, None)


def require_authenticated_user(allowed_roles=None):
    session_user = st.session_state.get("user")

    if not isinstance(session_user, dict) or not session_user.get("id"):
        st.info("Please sign in to continue.")
        st.stop()

    authenticated_at = st.session_state.get("authenticated_at")

    if (
        not isinstance(authenticated_at, datetime)
        or authenticated_at.tzinfo is None
    ):
        clear_user_session()
        st.warning("Your session is invalid. Please sign in again.")
        st.stop()

    session_age = datetime.now(timezone.utc) - authenticated_at

    if session_age >= timedelta(hours=settings.session_max_age_hours):
        clear_user_session()
        st.warning("Your session has expired. Please sign in again.")
        st.stop()

    if not ping_database():
        st.error("MongoDB is unavailable.")
        st.stop()

    db = get_database()

    record = UserRepository(db).by_id(session_user["id"])

    if not record or not record.get("is_active", False):
        clear_user_session()
        st.warning("Your account is unavailable. Please sign in again.")
        st.stop()

    current_user = {
        "id": str(record["_id"]),
        "name": record["name"],
        "email": record["email"],
        "role": record["role"],
    }

    if allowed_roles and current_user["role"] not in allowed_roles:
        st.error("You do not have permission to access this page.")
        st.stop()

    st.session_state.user = current_user

    return db, current_user
