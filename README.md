# AI-Powered Competency Gap & Personalized Learning Platform

A modular-monolithic Python application built with Streamlit, MongoDB, Pydantic and a provider-configurable Gemini integration. It evaluates a learner's skills, compares them with career requirements, generates personalized learning recommendations and tracks progress.

## Architecture (preserved)

- `pages/`: Streamlit presentation layer.
- `services/`: application and business logic.
- `models/`: Pydantic domain/input/output models.
- `database/`: MongoDB connection, collection definitions, indexes, seed data and repositories.
- `ai/`: LLM client, prompt templates, output parsing, guardrails and token estimation.
- `agents/`: custom Python agent orchestration and five specialist agents.
- `analytics/`: metrics, performance summaries and Plotly visualizations.
- `utils/`: validation, security, helpers and logging.
- `tests/`: automated tests for core workflows.

The application is a modular monolith. It does not use microservices, React, Node.js, LangChain or LangGraph.

## Requirements

- Python 3.11 or newer (Python 3.12 recommended).
- MongoDB Community Server running locally, or a MongoDB Atlas cluster.
- Gemini API key for AI features. The non-AI assessment and gap-analysis workflow works without it.
- Git is recommended.

## Windows setup

1. Extract the ZIP to a location such as `D:\Projects\competency-learning-platform`.
2. Open PowerShell in that folder.
3. Check Python: `python --version`.
4. Install dependencies in your selected Python installation: `python -m pip install -r requirements.txt`.
5. Copy `.env.example` to `.env` and edit the values:
   - Local MongoDB: `MONGODB_URI=mongodb://localhost:27017/`
   - `DATABASE_NAME=competency_learning_db`
   - Add the Gemini API key to `GEMINI_API_KEY`.
   - Replace `SECRET_KEY` with a long random value.
6. Start MongoDB.
7. Run `python -c "from database.connection import ping_database; print(ping_database())"`; expected output is `True`.
8. Run `streamlit run Home.py`.

No virtual environment is created by these instructions. If you prefer one, create it separately.

## MongoDB data location

The application connects to MongoDB; it does not decide where MongoDB stores its database files. To keep MongoDB data on the D: drive, configure the MongoDB server's `storage.dbPath` to a directory such as `D:\MongoDB\data` in the MongoDB server configuration, then start/restart the MongoDB service. Do not move a live database directory while the server is running. Back up data before changing `dbPath`.

## First administrator

Create the initial administrator from the project directory using `python -m scripts.create_admin`.

The script checks MongoDB, ensures database indexes, and securely prompts for the administrator email and password. The password is hashed with bcrypt before storage.

The bootstrap refuses to create another administrator if one already exists. Sign in through the Home page to access the Admin dashboard.

Do not store administrator credentials in `.env` or commit passwords.

## Included sample data

Seed data includes three sample career paths (Data Analyst, Python Developer, Web Developer), competencies, career-to-competency requirements, sample MCQs and learning-resource references. Review and replace these with institution-approved content before treating results as formal career-readiness assessments.

## Main learner workflow

1. Register and sign in.
2. Select a career goal.
3. Take the sample competency assessment.
4. Review the deterministic competency and gap analysis.
5. Generate an AI-assisted learning path (requires Gemini credentials).
6. Mark learning activities complete and monitor progress.
7. Retake assessments to compare attempts.

## Run tests

`python -m pytest -q`

The tests do not require a live MongoDB instance or real Gemini API key. Database integration tests are skipped unless a test MongoDB URI is supplied.

## Security and responsible use

- Never share or commit `.env`, API keys, database passwords or administrator passwords.
- Use HTTPS, secure hosting secrets, backups and least-privilege MongoDB users for deployment.
- This is an educational starter application, not a certified psychometric or hiring assessment.
- Assessment scores are estimates based on the included question bank. Missing evidence is not treated as zero.
- AI outputs are advisory, validated before use, and must be reviewed. AI does not directly change measured competency scores.
- The included session authentication is suitable as a local development foundation. Before public deployment, add stronger session-cookie controls, CSRF protection appropriate to the deployment, account recovery, email verification, audit review and operational monitoring.

## Functional boundaries

The project includes connected working foundations for authentication, career selection, assessment, deterministic gap analysis, AI recommendations, learning-path persistence, progress, notifications, admin seed/bootstrap, analytics and custom agent orchestration. External services require credentials. The included data and question bank are illustrative and should be reviewed/expanded.
