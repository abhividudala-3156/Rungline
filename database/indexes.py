def ensure_indexes(db):
    # Users
    db.users.create_index("email", unique=True)
    db.users.create_index("role")
    db.users.create_index("is_active")
    db.users.create_index([("created_at", -1)])

    # Careers and competencies
    db.careers.create_index("code", unique=True)
    db.careers.create_index([("is_active", 1), ("title", 1)])
    db.competencies.create_index("code", unique=True)

    # Career competency mappings
    db.career_competencies.create_index(
        [("career_code", 1), ("competency_code", 1)],
        unique=True,
    )

    # Assessment questions and attempts
    db.questions.create_index(
        [("career_code", 1), ("is_active", 1), ("competency_code", 1)]
    )
    db.assessment_attempts.create_index([("user_id", 1), ("created_at", -1)])

    # Competency profiles
    db.competency_profiles.create_index(
        [("user_id", 1), ("career_code", 1)],
        unique=True,
    )

    # Learning paths and progress
    db.learning_paths.create_index([("user_id", 1), ("created_at", -1)])
    db.learning_progress.create_index(
        [("user_id", 1), ("resource_id", 1)],
        unique=True,
    )
    db.learning_resources.create_index("competency_code")

    # Notifications
    db.notifications.create_index([("user_id", 1), ("created_at", -1)])

    # Audit logs
    db.audit_logs.create_index([("actor_id", 1), ("created_at", -1)])
    db.audit_logs.create_index([("created_at", -1)])
