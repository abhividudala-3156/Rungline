from datetime import datetime, timezone
from html import escape

import streamlit as st

from config import settings
from database.connection import get_database, ping_database
from database.indexes import ensure_indexes
from database.seed_database import seed_database
from services.auth_service import AuthService
from utils.auth import clear_user_session
from utils.logger import get_logger

logger = get_logger(__name__)

st.set_page_config(
    page_title=settings.app_name,
    page_icon="C",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2.5rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }

    .main-heading {
        font-size: 2rem;
        font-weight: 650;
        letter-spacing: -0.8px;
        margin-bottom: 0.4rem;
    }

    .sub-heading {
        color: var(--text-color);
        opacity: 0.65;
        font-size: 0.95rem;
        margin-bottom: 1.8rem;
    }

    .section-label {
        font-size: 0.78rem;
        font-weight: 650;
        letter-spacing: 1px;
        text-transform: uppercase;
        opacity: 0.6;
    }

    div[data-testid="stForm"] {
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 12px;
        padding: 1.4rem;
    }

    div.stButton > button,
    div.stFormSubmitButton > button {
        border-radius: 7px;
        font-weight: 550;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def initialize():
    if st.session_state.get("initialized"):
        return

    try:
        if not ping_database():
            st.session_state.db_ready = False
            st.session_state.db_error = "MongoDB is unavailable."
            return

        db = get_database()
        ensure_indexes(db)

        if settings.seed_on_start:
            seed_database(db)

        st.session_state.db_ready = True
        st.session_state.db_error = None
        st.session_state.initialized = True

    except Exception as exc:
        logger.error(
            "Application initialization failed (%s).",
            type(exc).__name__,
        )
        st.session_state.db_ready = False
        st.session_state.db_error = (
            "Database initialization failed. Check the application logs."
        )


initialize()

db_ready = st.session_state.get("db_ready", False)
user = st.session_state.get("user")


# --------------------------------------------------
# AUTHENTICATED HOME
# --------------------------------------------------

if user:
    safe_name = escape(user.get("name", "Learner"))

    st.markdown(
        '<div class="section-label">LEARNING PLATFORM</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="main-heading">Welcome back, {safe_name}</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sub-heading">'
        "Continue developing your competencies and working "
        "towards your career goals."
        "</div>",
        unsafe_allow_html=True,
    )

    left, right = st.columns([3, 1])

    with left:
        st.page_link(
            "pages/1_Dashboard.py",
            label="Open Dashboard",
            icon=":material/dashboard:",
            use_container_width=True,
        )

    with right:
        if st.button("Log out", use_container_width=True):
            clear_user_session()
            st.rerun()

    st.divider()

    st.markdown("### Workspace")

    col1, col2 = st.columns(2)

    with col1:
        st.page_link(
            "pages/3_Career_Goals.py",
            label="Career Goals",
            icon=":material/flag:",
            help="Select and manage your target career.",
            use_container_width=True,
        )

        st.page_link(
            "pages/4_Assessment.py",
            label="Competency Assessment",
            icon=":material/assignment:",
            help="Evaluate your current competencies.",
            use_container_width=True,
        )

        st.page_link(
            "pages/5_Competency_Gaps.py",
            label="Competency Gap Analysis",
            icon=":material/analytics:",
            help="Review your identified skill gaps.",
            use_container_width=True,
        )

    with col2:
        st.page_link(
            "pages/6_Learning_Roadmap.py",
            label="Learning Roadmap",
            icon=":material/map:",
            help="View your personalized learning path.",
            use_container_width=True,
        )

        st.page_link(
            "pages/7_AI_Mentor.py",
            label="AI Mentor",
            icon=":material/psychology:",
            help="Access AI-powered learning recommendations.",
            use_container_width=True,
        )

        st.page_link(
            "pages/8_Analytics.py",
            label="Performance Analytics",
            icon=":material/monitoring:",
            help="Review your learning performance.",
            use_container_width=True,
        )

    if user.get("role") == "admin":
        st.divider()
        st.markdown("### Administration")

        st.page_link(
            "pages/9_Admin.py",
            label="Administration Panel",
            icon=":material/admin_panel_settings:",
            use_container_width=True,
        )


# --------------------------------------------------
# LOGIN AND REGISTRATION
# --------------------------------------------------

else:
    st.markdown(
        '<div class="section-label">COMPETENCY DEVELOPMENT</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="main-heading">AI-Powered Competency Learning Platform</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sub-heading">'
        "Assess your skills, identify competency gaps, "
        "and develop a personalized learning roadmap."
        "</div>",
        unsafe_allow_html=True,
    )

    st.divider()

    if not db_ready:
        st.warning(
            "The database is currently unavailable. "
            "Registration and login are disabled."
        )

        if st.session_state.get("db_error"):
            st.caption(st.session_state.db_error)

    else:
        left, right = st.columns([1.1, 0.9], gap="large")

        with left:
            st.markdown("### Account access")
            st.caption("Sign in to continue your learning journey.")

            login_tab, register_tab = st.tabs(["Sign in", "Create account"])

            with login_tab:
                with st.form("login_form"):
                    email = st.text_input(
                        "Email address",
                        key="login_email",
                    )

                    password = st.text_input(
                        "Password",
                        type="password",
                        key="login_password",
                    )

                    login_submit = st.form_submit_button(
                        "Sign in",
                        use_container_width=True,
                    )

                if login_submit:
                    try:
                        authenticated_user = AuthService(get_database()).login(
                            email, password
                        )

                        if authenticated_user:
                            st.session_state.user = authenticated_user
                            st.session_state.authenticated_at = datetime.now(
                                timezone.utc
                            )

                            st.rerun()

                        else:
                            st.error("Invalid credentials or inactive account.")

                    except Exception as exc:
                        logger.error(
                            "Login failed (%s).",
                            type(exc).__name__,
                        )
                        st.error("Unable to sign in. Please try again.")

            with register_tab:
                with st.form("register_form"):
                    name = st.text_input("Full name")
                    new_email = st.text_input("Email address")

                    new_password = st.text_input(
                        "Password",
                        type="password",
                    )

                    confirm_password = st.text_input(
                        "Confirm password",
                        type="password",
                    )

                    register_submit = st.form_submit_button(
                        "Create account",
                        use_container_width=True,
                    )

                if register_submit:
                    if new_password != confirm_password:
                        st.error("Passwords do not match.")

                    else:
                        try:
                            AuthService(get_database()).register(
                                name,
                                new_email,
                                new_password,
                            )

                            st.success(
                                "Account created successfully. You can now sign in."
                            )

                        except Exception as exc:
                            logger.error(
                                "Registration failed (%s).",
                                type(exc).__name__,
                            )
                            st.error(
                                "Unable to create the account. "
                                "Check your details and try again."
                            )

        with right:
            st.markdown("### Platform overview")
            st.write(
                "A centralized environment for competency "
                "assessment and personalized skill development."
            )

            st.divider()

            st.markdown("**Competency assessment**")
            st.caption("Measure current skills against career requirements.")

            st.markdown("**Intelligent gap analysis**")
            st.caption("Identify competencies that need improvement.")

            st.markdown("**Personalized learning**")
            st.caption("Generate structured learning recommendations.")

            st.markdown("**Progress analytics**")
            st.caption("Monitor development and learning progress.")


st.divider()

st.caption("AI-Powered Competency Gap & Personalized Learning Platform")
