FROM python:3.11-slim

WORKDIR /app

# libgomp.so.1 is required by libtorch_cpu.so and is not shipped in python:3.11-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# CPU-only torch: the embedding model runs on CPU here, CUDA wheels are ~3GB of dead weight
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model at build time so container startup
# does not depend on network access (cache lives in /model-cache).
ENV HF_HOME=/model-cache
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
ENV HF_HUB_OFFLINE=1

# Copy source application (server.py + config.py + job_ingestion.py and any future module)
COPY *.py ./

ENV PYTHONUNBUFFERED=1

EXPOSE 3000

# Run FastMCP server (transport controlled by MCP_TRANSPORT: sse | streamable-http | stdio)
CMD ["python", "server.py"]
