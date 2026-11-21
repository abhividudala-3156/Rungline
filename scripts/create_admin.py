from getpass import getpass

from pymongo.errors import PyMongoError

from database.connection import close_connection, get_database, ping_database
from database.indexes import ensure_indexes
from database.repositories.audit_repository import AuditLogRepository
from services.auth_service import AuthService


def main():
    try:
        if not ping_database():
            print("MongoDB is unavailable. Check your database connection.")
            return 1

        db = get_database()

        ensure_indexes(db)

        if db.users.count_documents({"role": "admin"}) > 0:
            print("An administrator already exists. No account was created.")
            return 1

        print("\nInitial Administrator Bootstrap")
        print("--------------------------------")

        email = input("Administrator email: ").strip()
        password = getpass("Administrator password: ")
        confirmation = getpass("Confirm administrator password: ")

        if password != confirmation:
            print("Passwords do not match. No account was created.")
            return 1

        service = AuthService(db)

        user_id = service.bootstrap_initial_admin(email, password)

        actor = {
            "id": user_id,
            "email": email.strip().lower(),
            "role": "admin",
        }

        try:
            AuditLogRepository(db).record(
                actor=actor,
                action="auth.initial_admin.bootstrap",
                outcome="success",
                target_type="platform",
                target_id=user_id,
                details={"operation": "initial_admin_bootstrap"},
            )
        except (PyMongoError, ValueError):
            print(
                "\nAdministrator account was created, but its audit "
                "record could not be saved. Investigate the audit log."
            )
            return 1

        print("\nAdministrator account created successfully.")
        print("You can now sign in through the application.")

        return 0

    except ValueError as exc:
        print(f"\nAdministrator bootstrap failed: {exc}")
        return 1

    except PyMongoError as exc:
        print(
            "\nDatabase operation failed "
            f"({type(exc).__name__}). No success was reported."
        )
        return 1

    finally:
        close_connection()


if __name__ == "__main__":
    raise SystemExit(main())
