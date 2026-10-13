FROM python:3.11-slim

WORKDIR /app

# Build context is server/ so the shared SSE client from mcp-server/ is reachable.
COPY backend-server/backend_server.py backend-server/load_mcp_client.py backend-server/handle_header.py backend-server/handle_search.py ./
COPY mcp-server/mcp_sse_client.py ./

ENV PYTHONUNBUFFERED=1

EXPOSE 3100

CMD ["python", "backend_server.py"]
