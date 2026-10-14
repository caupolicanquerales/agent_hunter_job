# Agent Hunter Job

> A multi-agent platform that searches job boards, scores every posting against a
> candidate profile, persists the ranked results as embeddings in a vector
> database, and serves them to a filterable dashboard.

`agent_hunter_job` is an end-to-end job-hunting pipeline orchestrated by AI agents.
It combines a **skill-driven multi-agent orchestrator**, deterministic **Python
stdlib scripts**, a **FastMCP gateway that upserts and semantically searches
postings in pgvector**, a **stdlib HTTP backend**, and an **Angular 22 dashboard**
that turns the scored offers into a filterable shortlist.

---

## Table of contents

- [Why this project](#why-this-project)
- [Features](#features)
- [High-level architecture](#high-level-architecture)
- [Multi-agent orchestration](#multi-agent-orchestration)
- [Persistence & search (MCP + pgvector)](#persistence--search-mcp--pgvector)
- [HTTP backend](#http-backend)
- [Frontend architecture](#frontend-architecture)
- [Repository structure](#repository-structure)
- [Data model](#data-model)
- [Scoring rubric](#scoring-rubric)
- [Tech stack](#tech-stack)
- [Getting started](#getting-started)
- [Configuration reference](#configuration-reference)
- [Design decisions](#design-decisions)
- [Roadmap](#roadmap)

---

## Why this project

Job hunting at senior level is a **filtering problem**: hundreds of postings,
most irrelevant, across dozens of boards. Doing this manually is slow and
inconsistent. Agent Hunter Job automates the loop:

1. **Discover** — fetch live offers from public RSS feeds and JSON APIs.
2. **Reduce** — keyword-prefilter to remove noise before spending LLM tokens.
3. **Judge** — score each remaining candidate against a structured profile.
4. **Persist** — embed and upsert the scored postings into pgvector.
5. **Serve & visualize** — expose semantic search over HTTP and render a ranked,
   filterable dashboard.

The design goal is **cheap, parallel, auditable**: deterministic scripts do the
heavy lifting, and LLM agents are reserved for the judgement step, running in
bounded parallel fan-out with a strict fan-in contract.

---

## Features

- **Skill-driven orchestration** — the primary agent classifies intent and injects
  only the skills it needs, on demand (never preloaded).
- **Parallel, isolated evaluation** — up to 5 `job-evaluator` sub-agents run
  concurrently, each owning a disjoint set of chunk files. Every instance redirects
  command output to its own per-chunk log files, so concurrent shells never
  interleave.
- **Deterministic stdlib scripts** — parsing, normalization, chunking, reading and
  writing of intermediate artifacts use only the Python standard library, with
  well-defined exit codes.
- **Atomic, concurrency-safe persistence** — the reporter writes each evaluation
  file atomically (temp file + `fsync` + `os.replace`) and serializes database
  ingestion across parallel processes with an advisory file lock + bounded retries.
- **MCP gateway** — a FastMCP server exposes `store_job_postings` (embed + upsert)
  and `search_job_postings` (cosine-similarity search) over SSE.
- **Local embeddings** — `sentence-transformers/all-MiniLM-L6-v2` (384 dims),
  CPU-only Torch, model baked into the image for offline startup.
- **HNSW vector index** — fast approximate cosine-similarity search over postings.
- **Stdlib HTTP backend** — a dependency-free controller that fronts the MCP
  search tool with a CORS-enabled REST endpoint for the browser.
- **Server-side pagination** — the search endpoint is page-based
  (`page`/`page_size`); the backend forwards an `offset` to pgvector and returns
  `total_results`, `total_pages` and navigation flags.
- **Angular 22 + SSR dashboard** — signals-based state, standalone components,
  responsive master/detail UI wired to the backend search endpoint, with paginated
  results and instant skill/remote filtering over the loaded page.

---

## High-level architecture

```mermaid
flowchart TB
    User([User])

    subgraph Orchestration["Orchestration layer — opencode / VS Code Copilot"]
        Orch["job-orchestrator (primary agent)"]
        Eval["job-evaluator (sub-agent, x N)"]
        Skills[["Skills (on-demand)<br/>search · filter · read · write · profile · launch · clean"]]
    end

    subgraph Acquisition["Data acquisition — Python stdlib"]
        Fetch["fetch_jobs.py<br/>(RSS + JSON APIs)"]
    end

    subgraph Services["Docker stack — server/mcp_server_postgres_vector.yml"]
        MCP["FastMCP server<br/>store_job_postings · search_job_postings"]
        Embed["sentence-transformers<br/>(all-MiniLM-L6-v2, 384d)"]
        DB[("Postgres + pgvector<br/>scraped_job_postings")]
        Backend["backend-server<br/>/api/jobs/search :3100"]
    end

    subgraph Files["Artifacts"]
        Opps["reports/job_opportunities.js"]
        Chunks["reports/chunk_XX.json"]
        Results["results/chunk_XX_evaluation.json"]
    end

    subgraph Frontend["Presentation — Angular 22 SSR"]
        Dashboard["Job Dashboard<br/>list · detail · filters"]
    end

    User -->|"find jobs"| Orch
    Orch --> Skills
    Skills --> Fetch
    Fetch --> Opps
    Opps -->|"prefilter"| Chunks
    Orch -->|"fan-out"| Eval
    Eval -->|"read chunk"| Chunks
    Eval -->|"score + write"| Results
    Results -->|"reporter: store_job_postings"| MCP
    Orch -->|"launch stack"| MCP
    MCP --> Embed
    Embed --> DB
    Backend -->|"search_job_postings"| MCP
    DB --> Backend
    Dashboard -->|"GET /api/jobs/search"| Backend
```

---

## Multi-agent orchestration

The orchestrator follows a fixed, deterministic flow. The key idea is that
**the orchestrator never evaluates jobs itself** — it plans, dispatches and
verifies, while sub-agents do the per-chunk work.

```mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant O as job-orchestrator
    participant W as job-search-web
    participant F as job-search-filter
    participant E as job-evaluator (x K)
    participant M as MCP stack

    U->>O: "Find remote Java jobs"
    O->>O: Classify intent (EN/ES)
    O->>O: Clean reports/ + results/
    O->>W: Inject skill + run fetch_jobs.py
    W-->>O: reports/job_opportunities.js
    O-->>U: Notify: N jobs fetched (before filtering)
    O->>F: Inject skill + run prefilter
    F-->>O: reports/chunk_01..N.json
    O->>M: Inject job-launch-mcp-server (before fan-out)
    M-->>O: Containers Up + /sse = 200
    O->>O: K = min(N, 5)
    par Parallel fan-out (isolated shells)
        O->>E: chunk_01.json
        O->>E: chunk_02.json
        O->>E: chunk_0N.json
    end
    E-->>O: results/chunk_XX_evaluation.json (files) + store_job_postings
    O->>O: Fan-in: count N results, retry misses
    O-->>U: Evaluations saved: N
```

**Invariants enforced by the flow**

- Skills are injected **on demand**, never preloaded.
- The user is **notified before** the filter runs (overwrites are part of the flow).
- `reports/` (every stale file) and `results/` are both cleaned **once** by the
  orchestrator at the start, before the fetch (step 3) — the filter skill and
  sub-agents never delete anything; evaluators only write their own
  `<chunk>_evaluation.json` (a full clean would wipe siblings and break the fan-in count).
- Fan-in verifies `N` result files via a **file count**, never by opening them.
- Max **5** concurrent evaluators to stay within rate limits.
- **Shell isolation.** The K evaluators share one terminal, so no instance prints
  command output to it: each redirects stdout/stderr to its own `<chunk>`-named
  files (e.g. `reports/.chunk_01.reader.json`, `results/.chunk_01.writer.log`) and
  reads them back. The orchestrator runs no command while evaluators run.
- **Explicit, non-shared I/O.** The evaluator passes the report as an explicit file
  argument (`reports/<chunk>_report.json`) — never via stdin/heredoc — so parallel
  instances cannot corrupt each other's input.

### Roles

| Agent | Mode | Responsibility |
|-------|------|----------------|
| `job-orchestrator` | primary | Classify intent, run scripts, fan-out/fan-in, launch the Docker stack |
| `job-evaluator` | sub-agent | Score each candidate in one chunk against the profile, write the report |

### Skills

Skills are the composable capabilities the agents inject as needed.

| Skill | Script / input | Output |
|-------|----------------|--------|
| `job-search-commands` | intent rules (EN/ES) | routing decision |
| `job-search-web` | `fetch_jobs.py` | `reports/job_opportunities.js`, `.opencode/opportunities/raw_jobs_DATE.json` |
| `job-search-filter` | `prefilter_job_opportunities.py` | `reports/chunk_XX.json` (5 jobs each) |
| `job-read-chunk-files` | `reader_chunk_opportunities.py` | parsed chunk object (redirected to `reports/.<chunk>.reader.json`) |
| `job-write-chunk-final` | `final_chunk_reporter.py <chunk> <report>` | `results/chunk_XX_evaluation.json` + pgvector upsert |
| `job-delete-all-files` | `delete_all_files_in_folder.py` | clean folders (files only, non-recursive) |
| `job-launch-mcp-server` | Docker Compose checks | DB + MCP containers Up, probe `200` |
| `user-profile` | candidate profile | fit guidance for scoring |

---

## Persistence & search (MCP + pgvector)

The FastMCP server (`server/mcp-server/server.py`) exposes two tools over the
**SSE transport** (default `http://127.0.0.1:3000/sse`):

| Tool | Arguments | Purpose |
|------|-----------|---------|
| `store_job_postings` | `postings: list[dict]` | Embed each evaluated job and upsert it into `scraped_job_postings`; returns ingestion metadata (`new_jobs_stored`, `jobs_updated`) |
| `search_job_postings` | `query: str`, `limit: int = 5`, `source: str \| None`, `offset: int = 0` | Embed the query and rank stored jobs by cosine similarity via the HNSW index; `offset` skips the first *k* matches for pagination and the payload reports the overall `total_results` |

```mermaid
flowchart LR
    subgraph Store["store_job_postings"]
        A["Evaluated job objects<br/>(evaluation JSON array)"] --> B["Build embedding text<br/>title + source + keywords + review + pros/cons"]
        B --> C["sentence-transformers<br/>384-dim vectors"]
        C --> D[("UPSERT into<br/>scraped_job_postings")]
        D --> E{"Row existed before upsert?"}
        E -->|no| F["new_jobs_stored++"]
        E -->|yes| G["jobs_updated++"]
    end

    subgraph Search["search_job_postings"]
        Q["query text"] --> QE["embed query"]
        QE --> S["ORDER BY embedding <=> query<br/>LIMIT n OFFSET k"]
        S --> SR["rows + similarity<br/>+ total_results (COUNT)"]
    end
```

**Design highlights**

- **Deterministic IDs** — `external_job_id` is `SHA-256` of the job link (falling
  back to `title|source|link`), so re-runs upsert instead of duplicating, keyed by
  the `UNIQUE (external_job_id, source)` constraint.
- **Text that is actually searchable** — the embedding is built from the scored
  fields (title, source, matched keywords, review, pros, cons), so similarity
  ranks against the evaluation, not raw HTML.
- **Raw payload passthrough** — `search_job_postings` also returns `raw_payload`
  (the original evaluated object, retained verbatim). Because `asyncpg` hands
  `JSONB` back as text, the row decoder JSON-parses it before serialization, so the
  dashboard's raw-payload viewer renders real JSON instead of an escaped string.
- **Connection pool** — a lazily-created `asyncpg.Pool` guarded by an
  `asyncio.Lock`, closed on lifespan shutdown.
- **Offline model** — the embedding model is downloaded at build time
  (`HF_HUB_OFFLINE=1`) so container start has no network dependency.
- **Shared stdlib client** — `server/mcp-server/mcp_sse_client.py` is a
  dependency-free JSON-RPC-over-SSE client, imported by both the host reporter
  script and the backend server (via `sys.path` / the Docker build context).

---

## HTTP backend

`server/backend-server/` is a **stdlib-only** HTTP controller (`ThreadingHTTPServer`,
no Flask/FastAPI) that fronts the MCP search tool for the browser. It is split into
focused modules: routing (`backend_server.py`), request handling
(`handle_search.py`), response/CORS headers (`handle_header.py`) and MCP access
(`load_mcp_client.py`). Default port **3100**.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness probe → `{"status": "ok"}` |
| `GET` | `/api/jobs/search?query=&page=&page_size=&source=` | Search jobs (query params, paginated) |
| `POST` | `/api/jobs/search` | Search jobs (JSON body `{query, page, page_size, source}`) |
| `OPTIONS` | `/api/jobs/search` | CORS preflight → `204` |

- `400` — missing `query`, non-integer `page`/`page_size`, or invalid JSON body.
- `404` — unknown path. `502` — the MCP search call failed.
- `page` defaults to `1`; `page_size` defaults to `20` and is clamped to `100`.
  The legacy `limit` param is still accepted as an alias for `page_size`.
- The response echoes `page`, `page_size`, `total_results`, `total_pages`,
  `has_next_page` and `has_previous_page` alongside `results`.
- CORS is allow-listed to the Angular dev origins by default
  (`http://localhost:4200`, `http://127.0.0.1:4200`).

---

## Frontend architecture

An **Angular 22** standalone, signals-first, SSR-enabled dashboard wired to the
backend search endpoint.

```mermaid
flowchart TB
    subgraph App["Angular application"]
        Root["App (router-outlet)"]
        Routes["app.routes.ts<br/>'' -> JobDashboard"]
        Dashboard["JobDashboard<br/>filters · metrics · layout"]
        List["JobList<br/>cards + pagination footer"]
        Detail["JobDetail<br/>description · score · salary · pros/cons"]
        Viewer["RawPayloadViewer<br/>JSON inspection"]
    end

    subgraph State["Reactive state"]
        Service["JobService<br/>signal&lt;JobModel[]&gt;"]
        Filtered["computed: filteredJobs"]
        Selected["computed: selectedJob"]
        SkillList["computed: availableSkills"]
        Metrics["computed: totalMatches / averageMatchPercentage"]
        Paging["signals: page · pageSize<br/>totalResults · totalPages<br/>hasNextPage · hasPreviousPage"]
    end

    subgraph HTTP["Backend access"]
        SSE["SseService.getJobs()"]
        SSEGet["SseGetService (HttpClient GET)"]
    end

    Backend["backend-server :3100<br/>/api/jobs/search"]

    Root --> Routes --> Dashboard
    Dashboard --> List
    Dashboard --> Detail
    Detail --> Viewer
    Service --> Filtered
    Service --> Selected
    Service --> SkillList
    Service --> Metrics
    Service --> Paging
    Dashboard --> Service
    List --> Service
    Detail --> Service
    Service --> SSE --> SSEGet --> Backend
```

**State model** — `JobService` is the single source of truth:

- `_jobs`, `_selectedJobId`, `_filters` plus pagination state
  (`_page`, `_pageSize`, `_totalResults`, `_totalPages`) are private `signal`s.
- Exposed as `asReadonly()`; mutations go through intent methods
  (`setKeyword`, `toggleSkill`, `setSortBy`, `requestJobs`, ...). Pagination is
  driven by `goToPage` / `nextPage` / `previousPage` / `setPageSize`, and exposes
  `page`, `pageSize`, `totalResults`, `totalPages`, `hasNextPage`, `hasPreviousPage`.
- Derived views (`filteredJobs`, `selectedJob`, `availableSkills`,
  `averageMatchPercentage`) are `computed()` — no manual subscriptions, no stale UI.
- Two request streams feed one search: keyword changes go through a **debounced**
  (300 ms) `searchRequest$`, while page navigation bypasses it via an immediate
  `pageRequest$`; both are merged before `switchMap` so a new page fires right away.
- `buildSearchParams()` sends `{ query, page, page_size }`; `applyPagination()`
  copies the response's `page`, `page_size`, `total_results`, `total_pages` back
  into the signals, and the response also echoes `has_next_page` /
  `has_previous_page`.
- Client-side facets (`remoteOnly`, selected skills) and sorting operate on the
  currently loaded page via `filteredJobs`; keyword/remote/skill changes reset to
  page 1 and re-query the backend.
- The REST response (`JobSearchResponse`) is mapped to the dashboard model by
  `toJobModel()`: the cosine `similarity` becomes `match_score`,
  `matched_keywords` → `required_skills`, `description_review` →
  `clean_description`, `evaluated_at` → `scraped_at`, and `raw_payload` is carried
  through verbatim so `RawPayloadViewer` can render the original JSON.

**UI bindings**

- `JobDashboard` owns the **skills dropdown** (a multi-select built from
  `availableSkills`). Each option is a checkbox bound with
  `[checked]` + `(change)` (one event per toggle, so selections don't cancel out);
  toggling updates `filters().selectedSkills` and immediately re-filters
  `filteredJobs`. A `document:click` listener closes the menu on outside clicks.
- `JobList` renders the **pagination footer**: a `start–end of total` summary,
  prev/next buttons (disabled at the bounds) and a windowed (max 5) set of
  jump-to page numbers.
- The header metrics pill reports overall `totalResults` and, when there is more
  than one page, `Page X/Y`.

> Note: `SseService`/`SseGetService` are named for their eventual streaming role,
> but currently perform a plain HTTP `GET` through Angular's `HttpClient`.

---

## Repository structure

```text
agent_hunter_job/
├── .opencode/
│   ├── agents/                  # opencode agent definitions (orchestrator + evaluator)
│   ├── skills/                  # Composable capabilities, each self-contained
│   │   ├── job-search-commands/ # Intent classification rules (EN/ES)
│   │   ├── job-search-web/      # fetch_jobs.py + portal constants
│   │   ├── job-search-filter/   # prefilter_job_opportunities.py + keywords
│   │   ├── job-read-chunk-files/# reader_chunk_opportunities.py
│   │   ├── job-write-chunk-final/# final_chunk_reporter.py
│   │   ├── job-delete-all-files/# delete_all_files_in_folder.py
│   │   ├── job-launch-mcp-server/# Docker/Compose health checks
│   │   └── user-profile/        # Candidate profile + fit guidance
│   └── opportunities/           # Raw fetched jobs (raw_jobs_YYYY-MM-DD.json)
├── .github/agents/              # Mirror of the agent definitions for VS Code Copilot
├── .vscode/settings.json        # Copilot tool/terminal auto-approval
├── frontend/
│   └── job-hunter-frontend/     # Angular 22 standalone + SSR dashboard
│       └── src/app/
│           ├── models/          # JobModel, ScrapedJobPosting, filters, sort options
│           ├── services/        # JobService (signals) · SseService · SseGetService
│           └── components/      # dashboard, list, detail, raw-payload viewer
├── reports/                     # Pipeline artifacts
│   ├── job_opportunities.js     # Portal-grouped fetched offers
│   └── chunk_XX.json            # Prefiltered candidate chunks (5 per file)
├── results/                     # Per-chunk evaluation reports
│   ├── chunk_XX_evaluation.json
│   └── .reporter.lock           # Cross-process ingestion lock
├── server/
│   ├── backend-server/          # Stdlib HTTP controller (:3100)
│   │   ├── backend_server.py    # Routing only
│   │   ├── handle_search.py     # GET/POST /api/jobs/search
│   │   ├── handle_header.py     # JSON + CORS headers
│   │   ├── load_mcp_client.py   # Imports the shared SSE client, calls the tool
│   │   └── Dockerfile
│   ├── mcp-server/              # FastMCP gateway (Python)
│   │   ├── server.py            # MCP tools: store_job_postings, search_job_postings
│   │   ├── job_ingestion.py     # Embed, upsert, similarity search
│   │   ├── mcp_sse_client.py    # Stdlib MCP-over-SSE client (host + backend)
│   │   ├── config.py            # Env-driven configuration
│   │   ├── Dockerfile           # CPU-only Torch + baked model
│   │   └── requirements.txt
│   ├── mcp_server_postgres_vector.yml  # Compose: jobs-db + jobs-mcp-server + backend-server
│   └── init.sql                 # pgvector schema + HNSW index
├── opencode.json                # Permissions for scripts and folders
└── README.md
```

---

## Data model

`scraped_job_postings` (Postgres 16 + `pgvector`):

| Column | Type | Notes |
|--------|------|-------|
| `id` | `UUID` | PK, `gen_random_uuid()` |
| `eval_id` | `VARCHAR(50)` | Evaluator id (`{chunk}-{position}`) |
| `external_job_id` | `VARCHAR(255)` | SHA-256 of the link (or `title\|source\|link`) |
| `title` | `VARCHAR(500)` | |
| `link` | `TEXT` | Original posting URL |
| `source` | `VARCHAR(255)` | e.g. `WeWorkRemotely_Backend`, `RemoteOK_Java` |
| `salary`, `salary_currency`, `salary_period` | `VARCHAR` | As parsed by the fetcher |
| `years_experience` | `VARCHAR(64)` | e.g. `5+ years` |
| `description_review` | `TEXT` | Evaluator's 2–3 sentence review |
| `matched_keywords` | `TEXT[]` | Prefilter keywords that matched |
| `score` | `SMALLINT` | `0–100`, `CHECK` constraint |
| `recommendation` | `VARCHAR(20)` | `APPLY` / `CONSIDER` / `SKIP` |
| `pros`, `cons` | `TEXT[]` | Evidence-backed matches / mismatches |
| `raw_payload` | `JSONB` | Original evaluated object, retained verbatim |
| `embedding` | `vector(384)` | all-MiniLM-L6-v2 |
| `evaluated_at` | `TIMESTAMPTZ` | Updated on every upsert |

**Constraints & indexes**

- `UNIQUE (external_job_id, source)` → idempotent upserts.
- `idx_jobs_embedding_hnsw` — HNSW index over `embedding vector_cosine_ops` for
  fast approximate nearest-neighbour search.
- `idx_jobs_recommendation`, `idx_jobs_score` — supporting filters/ranking.

### Pipeline artifacts

| File | Producer | Consumer |
|------|----------|----------|
| `reports/job_opportunities.js` | `job-search-web` | `job-search-filter` |
| `reports/chunk_XX.json` | `job-search-filter` | `job-evaluator` (via reader) |
| `results/chunk_XX_evaluation.json` | `job-evaluator` (via reporter) | pgvector / frontend |
| `results/.chunk_XX.writer.log` | reporter (redirected) | `job-evaluator` (read-back) |

---

## Scoring rubric

Each candidate is scored `0–100` and labelled `APPLY` / `CONSIDER` / `SKIP`.

| Weight | Dimension |
|-------:|-----------|
| 40 | Technical stack match (Java, Spring Boot, microservices, REST, Angular/Vue/TS) |
| 25 | Seniority & architecture (senior/lead, system design, modernization) |
| 20 | Domain (banking / fintech / enterprise / modernization) |
| 15 | Applied AI & modernization (Spring AI, multi-agent, orchestration) |

| Score | Recommendation |
|------:|----------------|
| 80–100 | `APPLY` |
| 60–79 | `CONSIDER` |
| 0–59 | `SKIP` |

Every report entry keeps the candidate's original fields (verbatim) and adds
`id`, `score`, `recommendation`, `pros` and `cons` — `pros` are evidence-backed
matches, `cons` are honest mismatches (empty when there are none). The dashboard
additionally surfaces the vector `similarity` as a match percentage.

---

## Tech stack

| Layer | Technology |
|-------|------------|
| Orchestration | opencode agents + skills / VS Code Copilot agents (Markdown-driven) |
| Acquisition & ETL scripts | Python 3 stdlib (`urllib`, `xml.etree`, `json`, `fcntl`) |
| MCP gateway | FastMCP (`mcp[cli]` v1), `asyncpg`, `pydantic` |
| Embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`, 384d), CPU Torch |
| Storage | PostgreSQL 16 + `pgvector` (HNSW, cosine) |
| HTTP backend | Python 3 stdlib (`http.server`, `json`, `http.client`) |
| Containerization | Docker Compose |
| Frontend | Angular 22, standalone components, signals, SSR, Vitest |

---

## Getting started

### Prerequisites

- Docker + Docker Compose
- Python 3.11+
- Node.js (Angular 22 requires a modern Node) + npm
- Optional: [opencode](https://opencode.ai) or VS Code with GitHub Copilot to run
  the agent pipeline

### 1. Launch the Docker stack (database + MCP + backend)

`server/.env` only holds non-secret settings (e.g. `MCP_TRANSPORT=sse`). Build and
start all three services:

```bash
docker compose -f server/mcp_server_postgres_vector.yml up -d --build
```

Health checks:

```bash
curl -s -m 3 -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3000/sse    # MCP  -> 200
curl -s http://127.0.0.1:3100/health                                       # REST -> {"status":"ok"}
```

> Schema changes only apply to a fresh database volume: run
> `docker compose -f server/mcp_server_postgres_vector.yml down -v` before
> `up -d --build` if you edit `init.sql`.

### 2. Run the agent pipeline

Open the project in an opencode session (or use the mirrored VS Code Copilot
agents in `.github/agents/`) and ask for jobs:

```text
Find remote Java / Spring Boot job opportunities
```

The orchestrator fetches, prefilters, fans out to the evaluators and writes the
scored results into `results/`, then upserts each chunk into pgvector through the
MCP `store_job_postings` tool.

### 3. Run the frontend

```bash
cd frontend/job-hunter-frontend
npm install
npm start          # http://localhost:4200 (expects the backend on :3100)
npm test           # Vitest
npm run build      # production + SSR bundle
```

---

## Configuration reference

**MCP server** (`server/mcp-server/config.py`)

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `sse` | `sse` / `streamable-http` / `stdio` |
| `MCP_HOST` / `MCP_PORT` | `0.0.0.0` / `3000` | Bind address |
| `DATABASE_URL` | `postgresql://postgres:secretpassword@localhost:5432/jobs_db` | asyncpg DSN |

**Backend server** (`server/backend-server/`)

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_SERVER_URL` | `http://127.0.0.1:3000/sse` | MCP SSE endpoint |
| `BACKEND_HOST` / `BACKEND_PORT` | `0.0.0.0` / `3100` | Bind address |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:4200,http://127.0.0.1:4200` | Allowed browser origins |
| `SEARCH_DEFAULT_LIMIT` / `SEARCH_MAX_LIMIT` | `20` / `100` | Default / max `page_size` (`limit` is treated as a `page_size` alias) |

**Reporter script** (`final_chunk_reporter.py`)

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_SERVER_URL` | `http://127.0.0.1:3000/sse` | MCP SSE endpoint |
| `MCP_TIMEOUT_SECONDS` | `30` | SSE handshake/response timeout |
| `REPORTER_DB_LOCK_TIMEOUT_SECONDS` | `180` | Max wait for the ingestion lock |
| `REPORTER_DB_RETRIES` | `3` | Ingestion retry attempts |

---

## Design decisions

- **Deterministic scripts over eager LLM calls.** Parsing, normalization, chunking
  and persistence are pure Python. LLMs are only used where judgement is required,
  which keeps cost and latency predictable.
- **Two-stage filtering.** A keyword prefilter (`FILTER_KEYWORDS`) discards the
  obvious noise before any chunk reaches an agent — cheap recall now, precise
  scoring later.
- **Shared filesystem contract.** Sub-agents never return bulky payloads in prose;
  they read from `reports/` and write to `results/` through validated scripts with
  explicit exit codes. This makes the fan-in a simple, verifiable file count.
- **Bounded parallelism with isolated shells.** A hard cap of 5 concurrent
  evaluators respects provider rate limits, and each instance redirects its output
  to per-chunk log files so a shared terminal never interleaves their streams.
- **Crash-safe, concurrency-safe writes.** Evaluations are written with
  temp-file + `os.replace`; database ingestion is serialized with an advisory
  `flock` and retried. A failed DB sync degrades to a `Warning:` — the file stays
  the source of truth.
- **Stdlib at the edges.** Both the acquisition scripts and the HTTP backend avoid
  third-party runtimes, so they run anywhere Python does (and Docker images stay
  small).
- **Idempotent, evaluation-aware ingestion.** Content-addressed `external_job_id` +
  `ON CONFLICT` upserts make re-runs safe, and embeddings are built from the scored
  fields so semantic search ranks against the evaluation.
- **Reactive, typed frontend state.** Angular signals provide derived state with
  zero manual subscription management and full type-safety over `JobModel`.

---

## Roadmap

- [x] Wire the frontend to real data (backend `/api/jobs/search` → pgvector).
- [ ] Persist evaluation reports into Postgres for history and trend tracking.
- [ ] Expose a profile-embedding endpoint so the dashboard ranks against the
      candidate profile directly.
- [ ] Trigger a fresh pipeline run from the dashboard.
- [ ] Add CI (lint + tests for the Python scripts and the Angular app).

---

## License

_Add your license here (e.g. MIT)._ Built as a personal portfolio project.
