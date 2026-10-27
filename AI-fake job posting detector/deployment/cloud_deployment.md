# Cloud deployment (Azure example)

The same container runs on AWS (ECS/App Runner + RDS) with equivalent services.

```
Users -> Azure Load Balancer / Front Door -> App Service or Container Apps (FastAPI + frontend)
                                                  |-> Azure Database for MySQL
                                                  |-> LLM API (OpenAI or Azure OpenAI)
Azure Container Registry holds the image.
```

## Steps

1. **Train the model locally** with the real dataset: `python -m ml.train`. This creates `artifacts/model.joblib`.
2. **Build and push the image**
   ```bash
   az acr login --name <registry>
   docker build -f deployment/Dockerfile -t <registry>.azurecr.io/jobguard-ai:0.1.0 .
   docker push <registry>.azurecr.io/jobguard-ai:0.1.0
   ```
3. **Create Azure Database for MySQL** (flexible server). Create a `jobguard` database and a dedicated user. The app creates its tables on first start (or run `app/database/schema.sql`).
4. **Create the app** (App Service for Containers or Container Apps) from the pushed image and set these application settings:

   | Setting | Value |
   | ------- | ----- |
   | `APP_ENV` | `production` |
   | `SECRET_KEY` | random 32+ characters (store in Key Vault) |
   | `DATABASE_URL` | `mysql://user:password@<server>.mysql.database.azure.com:3306/jobguard` |
   | `LLM_PROVIDER` | `openai`, `azure` or `none` |
   | `LLM_API_KEY` | from Key Vault |

5. **Check** `https://<app>/health` returns `{"status":"ok","database":true,"model_loaded":true}`.

## Production checklist

- Serve over HTTPS only; the app refuses to start in production with the default `SECRET_KEY`.
- Keep secrets in Key Vault or app settings, never in the image or the repository.
- The rate limiter is per process. With several instances use a shared limiter (for example Redis) or one at the gateway.
- Changing SECRET_KEY signs every user out, so plan rotation.
- Behind a proxy the client IP seen by the app is the proxy's; configure forwarded headers before relying on per-IP limits.
- Add monitoring (health probe, logs, alerts on 5xx) and record the model version you deploy.
- Review the data you store: job descriptions can contain personal details. Add a retention policy and a way to delete accounts.
