# BotMesh runner

The runner is the BotMesh runtime plane. It authenticates with the backend, validates its plugin and service contracts, loads assigned bot configurations, and connects them to supported messenger adapters and external services.

For the recommended Docker setup, start with the repository [README](../README.md) and [getting-started guide](../docs/getting-started.md).

## Layout

- `bot_runner/core`: runtime, API client, contracts, registries, and adapter protocols.
- `bot_runner/core/adapters`: Telegram and MAX adapters.
- `bot_runner/plugins`: built-in plugin implementations.
- `bot_runner/services`: reusable service implementations.
- `bot_runner/tests`: contract, compatibility, and service tests.

## Required configuration

```dotenv
BACKEND_API_URL=https://botmesh.example.com/api/
BOT_RUNNER_API_KEY=replace-with-the-key-of-an-active-runner
```

`BACKEND_API_URL` must include `/api/`. The API key must belong to an active `BotRunner` record. Messenger tokens and external-service credentials depend on the bots assigned to the runner and should stay on the runner host.

## Start with Docker

From the repository root:

```bash
cp .env.runner.example .env.runner
docker compose -f deploy/runner.compose.yml up -d --build
docker compose -f deploy/runner.compose.yml logs -f runner
```

## Tests

```bash
docker compose -f compose.yml run --rm runner python -m unittest discover -s tests -v
```

Run backend and runner from the same release tag or Git commit. A contract mismatch is treated as a startup error rather than allowing an incompatible process to operate.
