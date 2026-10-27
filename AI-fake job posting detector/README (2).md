# AI-Based Fake Job Posting Detector (JobGuard AI)

A web application that analyzes a job advertisement and estimates how likely it is to be fraudulent. It combines a machine learning text classifier, transparent rule-based warning signs, and LLM-generated explanations.

> **Predictions are estimates, not proof of fraud or legitimacy.** Always verify an employer through official channels, and never pay money to get a job.

## Features

- Job posting analysis form with a fraud probability and risk level
- Machine learning classifier (TF-IDF + Logistic Regression or Random Forest, whichever scores better)
- Rule-based warning signs with the matching text quoted as evidence (upfront fees, vague duties, personal email or chat contact, unrealistic pay, and more)
- Plain-language explanation from an LLM, with an automatic template fallback
- Accounts, saved analysis history, and a model performance dashboard
- REST API with interactive docs, SQL storage (MySQL or SQLite), Docker and cloud deployment notes

## Technology

| Category | Technologies |
| -------- | ------------ |
| Language | Python 3.11+ |
| ML / NLP | scikit-learn, pandas, TF-IDF |
| Backend | FastAPI, Pydantic, PyJWT |
| Database | MySQL (deployment), SQLite (local development and tests) |
| Frontend | HTML, CSS, JavaScript (no build step) |
| Generative AI | OpenAI-compatible or Azure OpenAI chat API |
| Deployment | Docker, Azure (or AWS) |

## Quick start

```bash
git clone https://github.com/YOUR_USERNAME/ai-fake-job-posting-detector.git
cd ai-fake-job-posting-detector

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # Windows: copy .env.example .env
```

### 1. Train a model

With the real dataset (see [`data/README.md`](data/README.md)):

```bash
python -m ml.train --data data/fake_job_postings.csv
```

Or, to try the app immediately with **synthetic demo data** (metrics are not meaningful):

```bash
python -m ml.generate_sample_data
python -m ml.train --data data/sample_job_postings.csv
```

If you skip this step the app still runs, using only the rule-based warning signs.

### 2. Run the app

```bash
uvicorn app.main:app --reload
```

- Web app: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs

The default `DATABASE_URL` is a local SQLite file. Tables are created automatically on startup.

### 3. Use MySQL (optional)

Create a database and user, then set in `.env`:

```
DATABASE_URL=mysql://jobguard:your-password@localhost:3306/jobguard
```

Tables are created on startup from `app/database/schema.sql`.

### 4. Turn on LLM explanations (optional)

Set `LLM_PROVIDER=openai` (or `azure`) and `LLM_API_KEY` in `.env`. Without it, explanations come from a built-in template. Posting text is sent to the provider when you request an explanation, so do not use it with data you cannot share.

## API

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/health` | Application status |
| POST | `/predict` | Analyze a job posting |
| POST | `/explain` | Generate an explanation |
| GET | `/history` | Your saved analyses (sign-in required) |
| GET | `/model-info` | Model version and supported input fields |

Plus `/auth/*`, `/dashboard/*` and `/history/{id}`. Full details are in [`docs/api_documentation.md`](docs/api_documentation.md).

## Project structure

```text
app/          FastAPI backend (api, core, models, schemas, services, database)
frontend/     Web interface (HTML, CSS, JS)
ml/           Training, evaluation, preprocessing, synthetic data generator
data/         Dataset instructions (data files are not committed)
artifacts/    Trained model and metrics (not committed)
tests/        Automated tests
docs/         Architecture, API and database documentation
deployment/   Dockerfile and cloud deployment guide
```

## Tests

```bash
python -m pytest
```

## Model evaluation

Fraudulent postings are rare in real data, so accuracy alone is misleading. Training reports precision, recall, F1 and a confusion matrix for the fraudulent class, compares Logistic Regression with Random Forest, and saves the results for the dashboard. Record each run in [`ml/experiment_notes.md`](ml/experiment_notes.md).

## Limitations

- The classifier reflects its training data; public datasets are older and skewed toward certain job types and regions.
- The rule-based checks cannot confirm a company exists, and the salary check only understands US-dollar amounts.
- The probability is not calibrated, so treat it as a ranking signal rather than an exact chance.
- Login tokens are stored in the browser's `localStorage`; see [`docs/architecture.md`](docs/architecture.md) for the trade-off.

## Future improvements

- Calibrated probabilities and per-prediction feature explanations
- Suspicious URL and company-domain checks without opening untrusted links
- Password reset, email verification, and HttpOnly-cookie sessions
- Shared rate limiting and monitoring for multi-instance deployment
- Model version tracking and retraining on newer postings

## Deployment

See [`deployment/cloud_deployment.md`](deployment/cloud_deployment.md) for a Docker and Azure walkthrough.

## Disclaimer

This is an educational tool for spotting potential warning signs in job advertisements. Its predictions may be wrong and must not replace independent verification of an employer.

## License

MIT. See [`LICENSE`](LICENSE).
