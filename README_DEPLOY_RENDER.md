# Deploying Shield & Spear to Render

This guide shows how to deploy the project to Render using the provided `render.yaml` and `Procfile`.

Pre-reqs
- A Render account
- GitHub repository containing this project

Steps
1. Push your repo to GitHub.
2. On Render:
   - Go to "New" → "Import from GitHub" and select your repository.
   - Render will detect `render.yaml` and import services.
3. In the Render dashboard, go to the web service `shieldandspear-web`:
   - Set environment variables if needed (or let `render.yaml` generate `SECRET_KEY`).
   - Attach the Postgres database `shieldandspear-db` and copy the DATABASE_URL to the web service env if not automatically added.
   - If you plan to scale to multiple instances, add a Redis managed service and set `REDIS_URL` as an env var; put its value also as `SOCKETIO_MESSAGE_QUEUE`.
4. Deploy and monitor logs.

Notes
- Use `gunicorn -k eventlet` to support Socket.IO.
- Ensure `DATABASE_URL` env var points to the managed Postgres instance (Render will provide one).
- For SSL and domains, configure the domain inside Render and add DNS records.

If you want, I can prepare a `fly.toml` or `Dockerfile` instead — tell me which one you prefer.