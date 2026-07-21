# BotMesh backend

The backend is the BotMesh control plane. It is a Django application that provides the management dashboard, REST API, persistent configuration, access control, and runtime contract validation.

For the recommended Docker setup, start with the repository [README](../README.md) and [getting-started guide](../docs/getting-started.md).

## Main packages

- `bot_management`: bots, runners, installed plugins and services, actions, and dashboard views.
- `bot_templates`: reusable bot configuration templates.
- `accounts`: user-related models and views.
- `api`: runner- and bot-facing endpoints.
- `communication` and `events`: communication and event domain models.
- `core`: shared middleware.

## Management commands

Run commands from `backend/bot_platform` in a configured Python environment, or through the Compose backend service.

```bash
python manage.py migrate
python manage.py sync_builtin_catalog
python manage.py ensure_runner --name local-runner
python manage.py createsuperuser
python manage.py runserver
```

`sync_builtin_catalog` creates or updates built-in definitions without replacing configuration of existing installed plugins and services. `ensure_runner` reads `BOT_RUNNER_API_KEY` by default and creates or activates the corresponding runner record.

## Tests

The test settings expect PostgreSQL environment variables. The root Compose environment provides a ready database:

```bash
docker compose -f compose.yml run --rm backend python manage.py test
```
