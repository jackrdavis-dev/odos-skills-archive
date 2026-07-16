# Security and privacy

## Repository rule

No secret or authenticated session material belongs in this repository. That includes usernames used for login, passwords, API keys, cookies, session exports, one-time codes, browser profiles, private customer data, and full diagnostic dumps.

## Runtime authentication

The Release and optional Media publishing workflows are designed to reuse a user's already authenticated browser session. The repository contains instructions and non-secret destination configuration only. Authentication state remains outside the skill, staging area, logs, and Git history.

## Public configuration

URLs, edition prices, public Patreon tier identifiers, brand colors, and scheduling defaults are operational configuration rather than credentials. Review them before deployment because they can become stale or reveal business structure even when they are not secret.

## Before every public snapshot

- Run `scripts/verify-archive.ps1`.
- Search the complete Git diff for email addresses, tokens, passwords, cookies, and machine-specific home paths.
- Confirm generated customer files and campaign outputs are not staged.
- Inspect binary additions and their provenance.
- Verify that publishing configuration does not include private webhook URLs or access tokens.

## Reporting a problem

Do not open a public issue containing a secret. Revoke or rotate the exposed value first, remove it from the current tree and Git history, then use a private contact channel chosen by the repository owner.

