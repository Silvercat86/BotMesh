# Contributing

Keep backend and runner compatible within one change whenever a runtime contract changes.

## Development setup

Use the root [getting-started guide](docs/getting-started.md) to create the local Compose environment. Create a focused branch from the latest development revision and avoid committing local environment files or generated runtime data.

Before submitting a change:

1. run Django and runner tests;
2. create and inspect Django migrations;
3. update built-in definitions when plugin or service contracts change;
4. update deployment examples for new environment variables;
5. never add real credentials to fixtures or examples.

Use focused commits and explain migration or rollout requirements in the commit message.

## Pull requests

Describe the problem and solution, list verification commands, and call out database migrations, contract changes, new environment variables, and deployment-order requirements. Update user-facing documentation whenever behavior or setup changes.
