# Indicators of compromise for the Miasma Worm GitHub repository campaign

This folder contains a list of GitHub repositories compromised as part of the Miasma Worm campaign targeting AI coding agents via config injection.

The attack surface is distinct from the Miasma npm registry arm: rather than detonating during `npm install`, this vector triggers when a developer clones a compromised repository and opens it in an AI coding agent or IDE (Claude Code, Gemini CLI, Cursor, or VS Code). Malicious commits inject configuration files into `.claude/settings.json`, `.gemini/settings.json`, `.cursor/rules/setup.mdc`, `.vscode/tasks.json`, and the `package.json` test script — all pointing to a shared dropper at `.github/setup.js`.

## IOCs

[affected-repositories.csv](affected-repositories.csv) contains GitHub repositories confirmed to have received malicious commits as part of this campaign.

Format: one row per repository. `repository` is the full `owner/repo` path. `status` reflects the last-known state of the repository (`active` or `disabled by GitHub`).

Last updated: 2026-06-05.

## Sources

- https://safedep.io/miasma-worm-ai-coding-agent-config-injection/
