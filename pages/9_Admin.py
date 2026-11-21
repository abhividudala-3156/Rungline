import streamlit as st

from config import settings
from database.collections import COLLECTIONS
from database.indexes import ensure_indexes
from database.repositories.audit_repository import AuditLogRepository
from database.repositories.user_repository import UserRepository
from database.seed_database import seed_database
from utils.auth import require_authenticated_user

st.title("Administration")

st.caption("Manage platform reference data and monitor database activity.")


# Administrator authentication
session_user = st.session_state.get("user")

if session_user is None:
    st.info("Administrator sign-in required. Please sign in from the Home page.")
    st.stop()

db, user = require_authenticated_user(allowed_roles=["admin"])


# Administrator dashboard
st.success("Administrator access verified.")

audit_repository = AuditLogRepository(db)

st.divider()


# User statistics
st.subheader("User Overview")

user_repository = UserRepository(db)

users = user_repository.list_users()

total_users = db.users.count_documents({})
active_users = db.users.count_documents({"is_active": True})
admin_users = db.users.count_documents({"role": "admin"})
learner_users = db.users.count_documents({"role": "learner"})

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Users", total_users)

with col2:
    st.metric("Active Users", active_users)

with col3:
    st.metric("Learners", learner_users)

with col4:
    st.metric("Administrators", admin_users)


# User management overview
st.divider()

st.subheader("Registered Users")

if users:
    user_data = []

    for item in users:
        user_data.append(
            {
                "Name": item.get("name", "Not available"),
                "Email": item.get("email", "Not available"),
                "Role": item.get("role", "learner").title(),
                "Status": ("Active" if item.get("is_active", False) else "Inactive"),
            }
        )

    st.dataframe(
        user_data,
        width="stretch",
        hide_index=True,
    )

else:
    st.info("No registered users found.")


# Database overview
st.divider()

st.subheader("Database Overview")

st.write("Database Name:", settings.database_name)

collections = list(COLLECTIONS.values())
collection_data = []

for name in collections:
    count = db[name].count_documents({})

    collection_data.append(
        {
            "Collection": name,
            "Document Count": count,
        }
    )

st.dataframe(
    collection_data,
    width="stretch",
    hide_index=True,
)


# Administrative actions
st.divider()

st.subheader("Platform Maintenance")

st.warning(
    "These operations affect database configuration or reference data. "
    "Review the action before executing it."
)


def record_maintenance_action(action, outcome, operation):
    """Record a maintenance action without exposing database details."""
    try:
        audit_repository.record(
            actor=user,
            action=action,
            outcome=outcome,
            target_type="database",
            target_id=settings.database_name,
            details={"operation": operation},
        )
        return True

    except Exception:
        return False


col1, col2 = st.columns(2)

with col1:
    if st.button(
        "Verify / Recreate Database Indexes",
        width="stretch",
    ):
        try:
            ensure_indexes(db)
            operation_succeeded = True

        except Exception:
            operation_succeeded = False

        audit_saved = record_maintenance_action(
            action="database.indexes.ensure",
            outcome="success" if operation_succeeded else "failure",
            operation="ensure_indexes",
        )

        if operation_succeeded:
            st.success("Database indexes verified successfully.")
        else:
            st.error("The database index operation failed.")

        if not audit_saved:
            st.warning("The operation's audit record could not be saved.")

with col2:
    if st.button(
        "Add Missing Reference Data",
        width="stretch",
    ):
        try:
            seed_database(db)
            operation_succeeded = True

        except Exception:
            operation_succeeded = False

        audit_saved = record_maintenance_action(
            action="database.seed.ensure",
            outcome="success" if operation_succeeded else "failure",
            operation="seed_database",
        )

        if operation_succeeded:
            st.success(
                "Missing reference data added successfully. "
                "Existing records were left unchanged."
            )
        else:
            st.error("Adding missing reference data failed.")

        if not audit_saved:
            st.warning("The operation's audit record could not be saved.")


# Audit log overview
st.divider()

st.subheader("Administrative Audit Logs")

st.caption(
    "Recent administrator maintenance activities. "
    "The dashboard displays up to 100 records."
)

try:
    audit_logs = audit_repository.list_recent(user, limit=100)

    if audit_logs:
        audit_data = []

        for log in audit_logs:
            audit_data.append(
                {
                    "Timestamp (UTC)": log["created_at"].strftime("%Y-%m-%d %H:%M:%S"),
                    "Administrator": log.get("actor_email", "Not available"),
                    "Action": log.get("action", "Not available"),
                    "Target": log.get("target_id", "Not available"),
                    "Outcome": log.get("outcome", "Not available").title(),
                }
            )

        st.dataframe(
            audit_data,
            width="stretch",
            hide_index=True,
        )

    else:
        st.info("No audit records are available yet.")

except Exception:
    st.error("Audit records could not be loaded.")
