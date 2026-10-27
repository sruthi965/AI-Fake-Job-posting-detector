# Architecture

```
Browser (HTML/CSS/JS)  --JSON-->  FastAPI app
                                   |- api/        routes: auth, predict/explain, history, dashboard
                                   |- services/   preprocessing, risk_analysis, prediction_service, llm_service, auth_service
                                   |- database/   connection, repository, schema.sql  (MySQL, or SQLite for local use)
                                   '- core/        config, security
ml/ (offline)  train.py -> artifacts/model.joblib + metrics.json
```

## Request flow

1. The user submits a job posting on `analyze.html`; `analyze.js` calls `POST /predict`.
2. `prediction_service` builds a single text from the posting (`preprocessing.build_text`) and scores it with the TF-IDF classifier. `risk_analysis` independently looks for known scam patterns and returns indicators with quoted evidence.
3. The response shows the probability, indicators and a disclaimer on `result.html`.
4. "Get AI explanation" calls `POST /explain`. `llm_service` sends the prediction and indicators to the configured LLM (posting text is fenced as untrusted data) and falls back to a template explanation if the LLM is off or fails.
5. Signed-in users can save the analysis (`POST /history`), which is stored in `job_analysis` and shown on `history.html`.

## Design decisions

- **Headline probability comes from the classifier only.** The rule-based indicators explain and complement it but do not change the number, so published metrics describe the number users see. If no model is loaded, the rule score is used and labelled `rules-only`.
- **Shared preprocessing.** `app/services/preprocessing.py` is used by both training and inference to avoid train/serve skew.
- **Company name and salary are reduced to presence flags** in the model text so it does not memorise names or number formats; the salary check is a separate rule.
- **LLM output is never trusted:** it is parsed as strict JSON, length-limited, and rendered with `textContent`. Failures fall back to a template.
- **Auth:** PBKDF2-SHA256 password hashes, signed JWT bearer tokens, per-IP rate limits on login and registration, and per-user/IP limits on the LLM endpoint. History queries always filter by the signed-in user id.
- **Frontend security:** all server data is inserted with `textContent`; a strict Content-Security-Policy blocks inline scripts. The JWT is kept in `localStorage`, which is simple but readable by any script on the page; use HttpOnly cookies if you add third-party scripts.

## Known limitations

- Heuristic checks cannot verify that a company exists, and the salary rule only understands US-dollar amounts.
- The classifier reflects its training data (the public dataset is older and skewed to certain regions and job types).
- Model files are loaded with joblib (pickle): only load files you trained.
