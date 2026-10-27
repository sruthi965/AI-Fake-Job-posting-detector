# API documentation

Interactive docs are served at `/docs` (Swagger UI) and `/redoc` when the app is running. Percentages are numbers from 0 to 100.

| Method | Path | Auth | Description |
| ------ | ---- | ---- | ----------- |
| GET | `/health` | none | App, database and model status |
| POST | `/predict` | optional | Analyze a posting. With a token and `save_history: true` the result is stored |
| POST | `/explain` | optional | Plain-language explanation (rate limited: 10 per 10 minutes) |
| GET | `/model-info` | none | Scoring mode, model name, trained time, supported fields |
| GET | `/dashboard/model-performance` | none | Metrics saved by training, or `{"available": false}` |
| GET | `/dashboard/stats` | required | Your analysis counts |
| GET | `/history?page=1&page_size=10` | required | Your analyses, newest first |
| POST | `/history` | required | Save an analysis |
| GET | `/history/{id}` | required | One analysis with indicators and explanation |
| DELETE | `/history/{id}` | required | Delete one analysis |
| POST | `/auth/register` | none | Create an account, returns a token |
| POST | `/auth/login` | none | Returns a token |
| GET | `/auth/me` | required | Current user |

Send the token as `Authorization: Bearer <token>`.

## Example

```bash
curl -s localhost:8000/predict -H 'Content-Type: application/json' -d '{
  "job_title": "Remote Data Entry Assistant",
  "company_name": "Global Solutions Inc.",
  "description": "Help with our online operations. You must pay a small registration fee of $50 before starting.",
  "requirements": "Basic computer skills",
  "employment_type": "Full-time",
  "salary_range": "$500 - $800 per week"
}'
```

```json
{
  "prediction": "Fraudulent",
  "is_fraudulent": true,
  "fraud_probability": 91.3,
  "risk_level": "high",
  "risk_indicators": [{"code": "upfront_payment", "label": "Requests upfront payment or fees", "severity": "high", "evidence": "must pay"}],
  "model_used": "logistic_regression",
  "analysis_id": null,
  "disclaimer": "This prediction is an estimate, not proof of fraud. ..."
}
```

Input limits: `job_title` 2-255 chars, `description` 20-10,000, `requirements` up to 5,000, other optional fields up to 255/50/100. Errors use standard HTTP codes: 401 not signed in, 404 not found (also for other users' records), 409 duplicate email, 422 validation, 429 rate limited.
