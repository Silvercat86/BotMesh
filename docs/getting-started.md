# Getting started

This guide runs the complete BotMesh stack on one machine with Docker Compose. It is intended for evaluation and local development, not as a production hardening guide.

## 1. Prepare the environment

Install Git, Docker Engine, and Docker Compose v2. Confirm that Docker is running:

```bash
docker version
docker compose version
```

Clone the repository and enter its root directory:

```bash
git clone <repository-url>
cd BotMesh
```

Copy both example files:

```bash
cp .env.example .env
cp .env.runner.example .env.runner
```

On PowerShell, use:

```powershell
Copy-Item .env.example .env
Copy-Item .env.runner.example .env.runner
```

## 2. Set local secrets

Open `.env` and `.env.runner`. Replace all `replace-with-...` placeholders before exposing the application outside your machine.

Required backend values:

- `SECRET_KEY`: a long, unpredictable Django secret.
- `DB_PASSWORD`: the local PostgreSQL password.
- `ALLOWED_HOSTS`: hostnames accepted by Django.
- `CSRF_TRUSTED_ORIGINS`: complete browser origins, including scheme and port.

Required runner values:

- `BACKEND_API_URL`: `http://backend:8000/api/` in the local Compose network.
- `BOT_RUNNER_API_KEY`: a long random value used to identify this runner.

Keep the trailing `/api/` in `BACKEND_API_URL`. Local Compose supplies `.env.runner` to the backend as well, so `ensure_runner` can register that exact runner key.

The remaining credential variables are optional until a bot or service that needs them is configured.

## 3. Bootstrap the backend

Start PostgreSQL, Django, and Nginx:

```bash
docker compose -f compose.yml up -d --build db backend nginx
```

Apply database migrations and load the built-in catalog:

```bash
docker compose -f compose.yml exec backend python manage.py migrate
docker compose -f compose.yml exec backend python manage.py sync_builtin_catalog
```

Register the local runner using `BOT_RUNNER_API_KEY` from `.env.runner`:

```bash
docker compose -f compose.yml exec backend python manage.py ensure_runner --name local-runner
```

Create the first administrator and follow the interactive prompts:

```bash
docker compose -f compose.yml exec backend python manage.py createsuperuser
```

## 4. Start the runner

```bash
docker compose -f compose.yml up -d runner
```

Verify that all containers are running:

```bash
docker compose -f compose.yml ps
docker compose -f compose.yml logs --tail=100 backend runner
```

The runner intentionally refuses to start when its API key is unknown, its record is inactive, or its runtime contracts do not match the backend catalog. The log output should identify the rejected condition.

## 5. Open the dashboard

Visit <http://localhost:8080/dashboard/> and sign in with the superuser account.

A first bot normally requires:

1. a bot record assigned to `local-runner`;
2. a valid messenger token and selected platform;
3. one or more enabled plugins;
4. any services required by those plugins;
5. actions that map commands or events to plugin handlers;
6. the bot itself to be enabled.

The exact configuration fields are generated from the built-in plugin and service definitions. After changing runtime configuration, inspect runner logs to confirm that the bot was loaded successfully.

## Common operations

Follow logs:

```bash
docker compose -f compose.yml logs -f backend runner
```

Stop containers while preserving database and runner volumes:

```bash
docker compose -f compose.yml down
```

Stop containers and permanently delete local database and runner data:

```bash
docker compose -f compose.yml down -v
```

The `-v` form is destructive and should only be used when a clean environment is intended.

Rebuild after code or dependency changes:

```bash
docker compose -f compose.yml up -d --build
```

Apply backend changes after updating the repository:

```bash
docker compose -f compose.yml up -d --build db backend nginx
docker compose -f compose.yml exec backend python manage.py migrate
docker compose -f compose.yml exec backend python manage.py sync_builtin_catalog
docker compose -f compose.yml up -d --build runner
```

## Troubleshooting

### The dashboard does not open

Check `docker compose ps` and backend/Nginx logs. Confirm that `HTTP_PORT` is available and that `ALLOWED_HOSTS` includes the hostname used in the browser.

### CSRF verification fails

Add the exact browser origin to `CSRF_TRUSTED_ORIGINS`, including `http://` or `https://` and a non-default port. Restart the backend afterward.

### The runner is unauthorized

Confirm that `BOT_RUNNER_API_KEY` in `.env.runner` is the same value used by `ensure_runner`, and that the corresponding `BotRunner` record is active. Environment file changes require recreating the runner container:

```bash
docker compose -f compose.yml up -d --force-recreate runner
```

### Contract validation fails

Run backend and runner from the same Git commit or release tag, update the backend first, apply migrations, run `sync_builtin_catalog`, and then rebuild the runner.

### A bot does not start

Confirm that the bot, its plugins, and its required services are enabled; that it is assigned to the correct runner; and that its messenger credentials are valid. Runner logs contain the startup error for each rejected bot.
