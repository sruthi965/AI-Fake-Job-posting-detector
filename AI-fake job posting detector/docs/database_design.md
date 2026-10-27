# Database design

Two tables. The MySQL definition is in `app/database/schema.sql`; a SQLite equivalent used for local development and tests lives in `app/database/connection.py`.

## users

| Column | Type | Notes |
| ------ | ---- | ----- |
| id | INT, PK, auto increment | |
| full_name | VARCHAR(120) | |
| email | VARCHAR(255), unique | stored lower-case |
| password_hash | VARCHAR(255) | PBKDF2-SHA256, salted; never returned by the API |
| created_at | TIMESTAMP | |

## job_analysis

| Column | Type | Notes |
| ------ | ---- | ----- |
| id | INT, PK, auto increment | |
| job_title | VARCHAR(255) | |
| company_name | VARCHAR(255) | nullable |
| description | TEXT | |
| requirements, employment_type, salary_range | TEXT / VARCHAR | nullable |
| prediction | VARCHAR(50) | `Fraudulent` or `Legitimate` |
| fraud_probability | DECIMAL(5,2) | percentage, 0-100 |
| risk_indicators | TEXT | JSON list of indicators |
| explanation | TEXT | JSON object (summary, reasons, recommendation, source), nullable |
| model_used | VARCHAR(50) | model name or `rules-only` |
| created_at | TIMESTAMP | |
| user_id | INT, FK -> users(id), ON DELETE CASCADE | index on (user_id, id) |

Only signed-in users with history saving enabled have rows. Every query filters by `user_id`, and all SQL uses bound parameters.

Job descriptions can contain personal information; decide on a retention period before running this for real users.
