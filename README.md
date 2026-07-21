# BotMesh

BotMesh is a distributed control plane and runtime for messenger bots assembled from reusable plugins.

The Django backend stores bot configuration, plugin and service settings, actions, and access rights. One or more runners execute the bots and may live on separate servers. Before starting, a runner submits its actual plugin and service contracts to the backend and stops if they are incompatible.

> **Project status:** BotMesh is an early-stage portfolio and commercial project. Its API and deployment layout may change before the first stable release.

## Features

- Central dashboard for managing bots, plugins, services, actions, and access.
- Independent runners for Telegram and MAX integrations.
- Runtime contract validation between the backend and runner.
- Per-runner and per-bot API keys.
- Local Docker Compose environment and split production deployment.
- Built-in plugin and service catalog.

## Repository layout

```text
BotMesh/
├── backend/                  # Django control plane, API, and dashboard
│   └── bot_platform/
├── runner/                   # Bot runtime, plugins, and integrations
│   └── bot_runner/
├── deploy/
│   ├── backend.compose.yml   # PostgreSQL, Django, and Nginx
│   ├── runner.compose.yml    # Standalone runner
│   └── nginx.conf.template
├── docs/
│   ├── architecture.md
│   └── getting-started.md
├── compose.yml               # Complete local environment
├── .env.example              # Backend and database settings
└── .env.runner.example       # Runner settings and secrets
```

Backend and runner retain their original Git histories. They were joined into this monorepo with merge commits rather than squashed imports.

## Quick start

### Requirements

- Docker Engine with Docker Compose v2
- Git

Clone the repository, create local environment files, and replace the example secrets:

```bash
git clone <repository-url>
cd BotMesh
cp .env.example .env
cp .env.runner.example .env.runner
```

Generate independent random values for `SECRET_KEY`, `DB_PASSWORD`, and `BOT_RUNNER_API_KEY`. The value of `BOT_RUNNER_API_KEY` in `.env.runner` is also supplied to the backend during local setup, allowing `ensure_runner` to register the same key.

Start the database and backend first:

```bash
docker compose -f compose.yml up -d --build db backend nginx
docker compose -f compose.yml exec backend python manage.py migrate
docker compose -f compose.yml exec backend python manage.py sync_builtin_catalog
docker compose -f compose.yml exec backend python manage.py ensure_runner --name local-runner
docker compose -f compose.yml exec backend python manage.py createsuperuser
```

Then start the runner:

```bash
docker compose -f compose.yml up -d runner
```

Open the dashboard at <http://localhost:8080/dashboard/> and sign in with the administrator account. Check service status and logs with:

```bash
docker compose -f compose.yml ps
docker compose -f compose.yml logs --tail=100 backend runner
```

For the complete setup, first-bot checklist, troubleshooting, shutdown, and update instructions, see [Getting started](docs/getting-started.md).

## Core concepts

- **PluginDefinition** describes a supported plugin, its UI schema, runtime contract, actions, and required services.
- **BotPlugin** is an installed plugin with configuration and enabled state.
- **ServiceDefinition** and **BotService** provide reusable integrations such as an employee directory.
- **BotAction** maps a command or event to an exact handler of an installed plugin.
- **BotAccess** grants users access to a selected set of bots.
- **BotRunner** identifies a remote runner and authenticates it with an API key.

See [Architecture](docs/architecture.md) for the component boundaries and deployment sequence.

## Distributed deployment

The backend server runs PostgreSQL, Django/Gunicorn, and Nginx:

```bash
cp .env.example .env
docker compose --env-file .env -f deploy/backend.compose.yml up -d --build
docker compose --env-file .env -f deploy/backend.compose.yml exec backend python manage.py migrate
docker compose --env-file .env -f deploy/backend.compose.yml exec backend python manage.py sync_builtin_catalog
```

Create an active runner record in the Django admin or run `ensure_runner` with a securely transferred runner key. On the runner server:

```bash
cp .env.runner.example .env.runner
docker compose -f deploy/runner.compose.yml up -d --build
```

Set `BACKEND_API_URL` to the public HTTPS API URL, including the trailing `/api/`, and set `BOT_RUNNER_API_KEY` to the key registered in the backend. A public HTTPS backend address is required when the servers communicate over the internet.

Backend and runner should run the same release tag or, before releases exist, the same Git commit. Deploy the backend and migrations before updating runners.

## Configuration and secrets

Never commit `.env`, bot tokens, service-account JSON, API keys, or private keys. Example files contain placeholders only.

Google service-account credentials belong on the runner server and may be passed as base64-encoded JSON:

```dotenv
KEEPCAT_CREDENTIALS_BASE64=base64-encoded-service-account-json
```

`people_directory_service` uses this value when `service_account_b64` is absent from backend configuration, so the credential does not need to be stored in Django.

## Tests

Backend tests use PostgreSQL:

```bash
docker compose -f compose.yml run --rm backend python manage.py test
```

Runner tests:

```bash
docker compose -f compose.yml run --rm runner python -m unittest discover -s tests -v
```

CI runs both suites and checks that Django models have matching migrations.

## Contributing and security

Read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a change. Report sensitive vulnerabilities according to [SECURITY.md](SECURITY.md); do not publish credentials or exploit details in a public issue.

## License

BotMesh is available under the [MIT License](LICENSE).
