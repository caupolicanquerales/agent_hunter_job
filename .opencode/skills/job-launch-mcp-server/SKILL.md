---
name: job-launch-mcp-server
description: Ensures the containers of server/mcp_server_postgres_vector.yml (Postgres + MCP server) are running, starting them again if they are stopped, exited or missing. Use before the orchestrator calls any MCP method.
---

# Job Launch MCP Server

Bring up the MCP stack (`jobs-db`, `jobs-mcp-server`) when it is not running. Never assume it is up; never report ready before the checks below.

**Trigger** (EN/ES) before calling an MCP method: check/launch/start the MCP server, containers, database; "levantar el servidor MCP", "revisar contenedores", "iniciar la base de datos".

## Run (from project root)

1. Docker preflight: if `docker --version && docker compose version` fails, install per OS — Linux `curl -fsSL https://get.docker.com | sh && sudo systemctl enable --now docker`, macOS `brew install --cask docker`, Windows `winget install Docker.DockerDesktop`. Daemon stopped → `sudo systemctl start docker`.
   On `permission denied` (socket `root:docker`): **never ask the user for a password in chat** (it would be logged; your shell has no TTY). Stop and show the user the one-time fix to run in a terminal you open/focus for them: `sudo usermod -aG docker "$USER"` (they type the password there; log out/in or `newgrp docker`). Afterwards docker runs passwordless, no `sudo`.
2. Check `server/.env` has a real `APIFY_TOKEN`; if not, ask the user — never invent one.
3. Inspect: `docker compose -f server/mcp_server_postgres_vector.yml ps -a`. If any service is absent/exited/stopped/restarting → `docker compose -f server/mcp_server_postgres_vector.yml up -d --build` (rebuilds after code changes; waits for db healthcheck).
4. Verify both Up (db healthy) and probe `curl -s -m 3 -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3000/sse` prints `200` (stays open; PowerShell: `curl.exe`).

## Output

- Report "MCP stack already running" or launch result + final `ps`.
- Ready only when both containers are Up **and** probe `200`; if Up but probe fails, show `docker compose -f server/mcp_server_postgres_vector.yml logs --tail=50 jobs-mcp-server`.
- On failure report exact output; port conflict → edit host side of `ports:` (`127.0.0.1:5433:5432` example).
- Never claim readiness while a container is exited/restarting or `jobs-db` unhealthy. No triggers for fetch/filter/chunks (`job-search-web`, `job-search-filter`, `job-read-chunk-files`).