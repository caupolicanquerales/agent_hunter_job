---
name: job-launch-mcp-server
description: Ensures the containers of server/mcp_server_postgres_vector.yml (Postgres + MCP server) are running, starting them again if they are stopped, exited or missing. Use before the orchestrator calls any MCP method.
---

# Job Launch MCP Server

Bring up the MCP stack (`jobs-db`, `jobs-mcp-server`) when not running. Never report ready before the checks pass.

**Trigger** (EN/ES) before any MCP call: check/launch/start the MCP server, containers, database; "levantar el servidor MCP", "revisar contenedores", "iniciar la base de datos".

Compose file: `server/mcp_server_postgres_vector.yml` (run from project root).

## Run

1. **Docker preflight.** If `docker --version && docker compose version` fails, install per OS (Linux: `curl -fsSL https://get.docker.com | sh && sudo systemctl enable --now docker`; macOS: `brew install --cask docker`; Windows: `winget install Docker.DockerDesktop`). Daemon stopped: `sudo systemctl start docker`.
2. **Permission denied** (socket `root:docker`, Ubuntu):
   - Do **not** ask the user to type or run commands themselves, and do not ask for the password in chat.
   - Run `sudo usermod -aG docker "$USER"` in a visible VS Code terminal (`run_in_terminal`, mode `async`, so the terminal stays open). The `sudo` password prompt ("se requiere una contraseña") appears in that terminal; the user types the password there.
   - Wait for the terminal to finish with `get_terminal_output`. If it is still waiting for input, tell the user only: "Type your sudo password in the open terminal". **Never read, store, or send the password via `send_to_terminal` or chat.**
   - Exit code 0 means success. Run all docker commands via `sg docker -c "<command>"` in this session; no logout needed.
   - If `sudo` fails (wrong password, user not in sudoers) or the exit code is not 0, stop and report the exact output.
3. **Env check.** `server/.env` may hold only non-secret settings (e.g. `MCP_TRANSPORT`).
4. **Inspect first (mandatory on every run, never skip).** Run `sg docker -c "docker compose -f server/mcp_server_postgres_vector.yml ps -a"` (`sg` avoids the stale group session). If `jobs-db` and `jobs-mcp-server` are both Up and `jobs-db` is healthy, report "MCP stack already running" and go to step 5. Only if a service is absent, exited, stopped or restarting, run `sg docker -c "docker compose -f server/mcp_server_postgres_vector.yml up -d --build"`. Never run `up -d` without inspecting first.
5. **Verify.** Both containers Up and `jobs-db` healthy, then `curl -s -m 3 -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3000/sse` returns `200` (PowerShell: `curl.exe`).

## Output

- Report "MCP stack already running" or the launch result with the final `ps`.
- Ready only when both containers are Up, `jobs-db` is healthy, and the probe returns `200`.
- If Up but the probe fails, show `docker compose -f server/mcp_server_postgres_vector.yml logs --tail=50 jobs-mcp-server`.
- Port conflict: change the host side of `ports:` (e.g. `127.0.0.1:5433:5432`).
- Never claim readiness while a container is exited or restarting, or `jobs-db` is unhealthy.
- Not for fetch, filter or chunk tasks (`job-search-web`, `job-search-filter`, `job-read-chunk-files`).