# Build from the project root:
#   docker build -f deployment/Dockerfile -t jobguard-ai .
# Train a model first (python -m ml.train) so artifacts/model.joblib is included,
# or mount/bake it in at deploy time. Without it the app uses rule-based scoring only.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY ml ./ml
COPY frontend ./frontend
COPY artifacts ./artifacts

RUN useradd --create-home appuser && chown -R appuser /srv/app
USER appuser

ENV APP_ENV=production
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
