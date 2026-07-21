# Security policy

## Supported versions

BotMesh has not reached its first stable release. Security fixes are applied to the latest revision only; older commits and development snapshots are not supported.

## Secrets

Do not commit environment files, messenger tokens, API keys, private keys or service-account documents. Store backend and runner secrets separately because they have different trust boundaries.

If a secret is committed:

1. revoke or rotate it immediately;
2. remove it from Git history before publishing;
3. invalidate cached images and deployment variables;
4. document the incident without reproducing the secret.

## Reporting

Do not open a public issue containing exploit details or credentials. Until a dedicated security address is published, use the repository host's private vulnerability-reporting feature or contact the repository owner through a private channel listed on their profile.

Include the affected component and revision, reproduction steps, impact, and any suggested mitigation. Do not include real user data or active credentials. A response-time commitment will be published when a stable release and a permanent security contact are available.
