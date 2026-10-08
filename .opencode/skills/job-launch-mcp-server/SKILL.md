---
name: job-launch-mcp-server
description: Ensures the containers of server/mcp_server_postgres_vector.yml (Postgres + MCP server) are running, starting them again if they are stopped, exited or missing. Use before the orchestrator calls any MCP method.
---

# Job Launch MCP Server

Brings the MCP stack (`jobs-db`, `jobs-mcp-server`) up when it is not running. Never assume containers are up; never report ready without the checks below.

**Trigger** (EN/ES) before calling an MCP method: "launch/check the MCP server", "check the containers", "start the database", "levantar el servidor MCP", "revisar contenedores", "iniciar la base de datos".

## Run

From the project root (`agent_hunter_job`):

1. If `docker --version && docker compose version` fails, install per OS (`uname -s`): Linux `curl -fsSL https://get.docker.com | sh && sudo systemctl enable --now docker`; macOS `brew install --cask docker`; Windows `winget install Docker.DockerDesktop`. Daemon not running → Linux: `sudo systemctl start docker`. On `permission denied` (Ubuntu/Debian): `sudo usermod -aG docker "$USER" && newgrp docker` (no logout needed; non-interactive shells: wrap commands in `sg docker -c '<cmd>'`; no sudo → prefix commands with `sudo`).
2. Ensure `server/.env` has a real `APIFY_TOKEN` (not `apify_api_REPLACE_ME`); if missing, ask the user — never invent one.
3. Check states: `docker compose -f server/mcp_server_postgres_vector.yml ps -a`. If any service is absent/exited/stopped/restarting: `docker compose -f server/mcp_server_postgres_vector.yml up -d --build` (`--build` rebuilds after code changes; waits for db healthcheck).
4. Verify `ps` shows both Up (db healthy) and `curl -s -m 3 -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3000/sse` prints `200` (`-m 3` timeout normal, `/sse` stays open; PowerShell: `curl.exe`).

## Output

- Report "MCP stack already running" or the launch result + final `ps` state.
- Announce ready only when both containers are Up and the probe returns 200; if Up but probe fails, show `docker compose -f server/mcp_server_postgres_vector.yml logs --tail=50 jobs-mcp-server`.
- On failure report exact command output; port conflict → edit host side of `ports:` in `server/mcp_server_postgres_vector.yml` (e.g. `127.0.0.1:5433:5432`).
- Never claim readiness while a container is exited/restarting or `jobs-db` unhealthy. No triggers for fetch/filter/chunks (`job-search-web`, `job-search-filter`, `job-read-chunk-files`).
