# Scriptly

A web application for browsing, reading, and asking questions about
Shakespeare's plays. It loads the
[Shakespeare dataset](https://www.kaggle.com/datasets/kingburrito666/shakespeare-plays)
(`Shakespeare_data.csv`) into MySQL, serves it through a Django REST API, and
presents it in a vanilla JavaScript reader frontend — with a full RAG pipeline
(ChromaDB + LangGraph + Groq) powering an "Ask Scriptly" AI assistant.

## Architecture

```
Shakespeare_data.csv
        │
        ▼  load_to_mysql.py (pandas + SQLAlchemy)
MySQL (scriptly_db)
        │                                   ingest_data.py (spaCy NER +
        ▼  Django + DRF backend (:8000) ◄── sentence-transformers embeddings)
        │         │
        │         ▼
        │  ChromaDB (chroma_db/) ── shakespeare_speeches + semantic_cache collections
        │         │
        │         ▼  RAGRetriever → ShakespeareAgent (LangGraph graph)
        ▼  fetch() from frontend/app.js
Vanilla HTML/CSS/JS frontend (:5500) ── left sidebar: reader navigation
                                     └─ right sidebar: Ask Scriptly + insights
```

Four independent pieces:

1. **Data loader** — one-off script that parses the CSV and builds a relational schema in MySQL.
2. **Backend** (`backend/`) — Django + DRF app exposing a read-only JSON API plus the RAG endpoints.
3. **Vector ingestion** (`ingest_data.py`) — embeds every speech into ChromaDB with spaCy-extracted entity metadata.
4. **Frontend** (`frontend/`) — no build step; plain HTML/CSS/JS that calls the API with `fetch()`.

## Data pipeline

`load_to_mysql.py` reads `Shakespeare_data.csv`, where each row is a single
line of dialogue with columns `Play`, `Player`, `PlayerLine`, and
`ActSceneLine` (format `act.scene.line`). It then:

1. **Deduplicates entities** using in-memory maps keyed on play name,
   `(play_id, player)` for characters, and `(play_id, act, scene)` for scenes.
2. **Merges consecutive lines** by the same character within the same scene
   into a single **speech**, tracking `start_line` / `end_line` and joining the
   text lines with `\n`. Rows without a `Player` (stage directions / scene
   headers) only register the scene, not a speech.
3. **Loads via pandas `to_sql`** through a SQLAlchemy engine
   (`mysql+mysqlconnector://...@localhost/scriptly_db`), dropping existing
   tables first with `FOREIGN_KEY_CHECKS = 0`.
4. **Applies constraints and indexes** afterward with raw SQL:
   primary keys, foreign keys between all tables, an index on
   `characters(name)`, a composite index on `scenes(play_id, act, scene)`,
   and `speeches(play_id, character_id)`.

Resulting volumes: ~36 plays, ~1,100 characters, 737 scenes, 30,045 speeches.

### Database schema

Full details in [schema.md](schema.md). Summary:

| Table | Purpose |
|-------|---------|
| `plays` | `id`, `name` |
| `characters` | Per-play character names, FK to `plays` |
| `scenes` | `(play, act, scene)` tuples, FK to `plays` |
| `speeches` | Continuous blocks of dialogue; FKs to `plays`, `characters`, `scenes`; denormalized `act`/`scene` columns |

## Vector ingestion pipeline

`ingest_data.py` (run once, after `load_to_mysql.py`) builds the vector store
at `./chroma_db/` using ChromaDB's persistent client:

1. Reads every speech from MySQL with its relational metadata
   (play, character, act, scene).
2. Runs **spaCy** (`en_core_web_sm`) NER over each speech in batches and
   extracts `PERSON` / `GPE` / `ORG` entities as metadata.
3. Formats each speech as a readable document
   (`Play: … | Act: … Scene: … | Speaker: … \n Dialogue: …`) and embeds it with
   **sentence-transformers/all-MiniLM-L6-v2** (384-dim, CPU-friendly) in
   batches of 256.
4. Stores everything in the `shakespeare_speeches` collection keyed by the
   deterministic ID `speech_{id}` — so vector results can be deep-linked back
   to the reader.

## RAG pipeline & semantic caching

The AI assistant is served by `POST /api/ask/`:

```
User question
     │
     ▼  EmbeddingService.embed_query()
Semantic cache check (ChromaDB "semantic_cache", L2 distance < 0.15)
     │
     ├─ HIT  → return cached answer            ⚡ typically ~0.02s
     │
     └─ MISS → top-5 retrieval from "shakespeare_speeches"
                │
                ▼  LangGraph agent (api/agent.py)
           grade ──(all irrelevant? rewrite query, re-fetch, max 2 loops)──┐
              ▲◄───────────────────────────────────────────────────────────┘
              ▼
           generate (Groq LLM synthesis over graded context)
                │
                ▼  answer + citations saved to semantic cache
```

- **LLM**: Groq-hosted `openai/gpt-oss-20b` (`temperature=0`), via `langchain-groq`.
- **Grader**: structured output (`json_schema` mode) scoring each document
  relevant/irrelevant; grading failures fall through and keep the document.
- **Citations**: each retrieved document carries ingestion metadata
  (`play_name`, `act`, `scene`); deduplicated citations are returned with the
  answer *and* stored inside the cache so cached hits keep deep links.
- **Latency**: measured end-to-end per request. Typical numbers:
  LangGraph pipeline ≈ 5–8s on a miss, semantic-cache hit ≈ 0.02–0.04s.

## Backend

Django project at `backend/scriptly_backend/` with a single app `backend/api/`.

- **Models** (`api/models.py`) map onto the tables created by the loader with
  `managed = False` — Django never migrates the schema; it only reads.
- **Serializers** (`api/serializers.py`) flatten relations into JSON, e.g.
  speech responses include `character_name`.
- **Views** (`api/views.py`) are DRF `APIView`s doing read-only ORM queries,
  ordered by act/scene and insertion order so scripts render in sequence.
- **URLs** (`api/urls.py`) mount everything under `/api/`.
- **CORS** (`scriptly_backend/cors.py`) is a small custom middleware adding
  `Access-Control-Allow-Origin: *` so the separately-served frontend can call
  the API.

### API endpoints

Base URL: `/api/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/plays/` | All plays (id, name), ordered by name |
| GET | `/api/plays/{play_id}/` | Single play detail |
| GET | `/api/plays/{play_id}/scenes/` | Scenes of a play, ordered by act/scene |
| GET | `/api/scenes/{scene_id}/speeches/` | Full script of a scene in order |
| GET | `/api/plays/{play_id}/characters/{name}/speeches/` | All lines of a character in a play (case-insensitive) |
| POST | `/api/ask/` | RAG question answering; body `{"query": "…"}`; returns `answer`, `source`, `time_seconds`, `citations` |
| GET | `/api/scenes/{scene_id}/insights/` | spaCy entity insights for a scene: top characters, locations, themes |

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/ask/ \
  -H "Content-Type: application/json" \
  -d '{"query": "Compare Macbeth and Lady Macbeth'"'"'s guilt"}'
```

```json
{
  "answer": "…",
  "source": "groq_langgraph_pipeline",   // or "semantic_cache"
  "time_seconds": 4.8406,
  "citations": [
    {"play_name": "macbeth", "act": 2, "scene": 2},
    {"play_name": "macbeth", "act": 1, "scene": 7}
  ]
}
```

## Frontend

`frontend/index.html` + `styles.css` + `app.js`, served by any static server
(no bundler, no framework). Three-column layout — left sidebar (navigation),
center reader, right AI sidebar. `app.js`:

- Holds the API base URL (`http://127.0.0.1:8000/api`) in the `API_BASE`
  constant at the top of the file.
- Fetches the play list once, filters it client-side as you type.
- On play selection, fetches scenes, then lazily fetches speeches per scene
  and renders speaker names plus stage directions in a reader view with
  prev/next scene navigation.
- Character search calls the per-character speeches endpoint and displays
  matching lines.
- Includes a dark/light theme toggle.

### Ask Scriptly (right sidebar)

- Natural-language input posting to `POST /api/ask/`; answers stack as cards,
  newest first.
- **Source & latency badge** on every answer:
  - ⚡ `Cached (0.02s)` when served from ChromaDB's semantic cache
    (`source: semantic_cache`)
  - 🤖 `LangGraph Pipeline (5.1s)` for live retrieval + LLM synthesis
    (`source: groq_langgraph_pipeline`)
- **Interactive citation jumping**: citation buttons under each answer deep-link
  the reader to the exact play → act → scene. Matching is case-insensitive on
  play names (the dataset stores them lowercased); if another play is cited,
  it is selected and its scene loaded automatically.
- **Scene Insights panel**: while reading a scene, the panel shows key entities
  extracted from that scene via spaCy — characters, locations, and themes —
  rendered as chips with mention counts, cached client-side per scene.

## Running locally

Requirements: Python 3, MySQL running locally, a database `scriptly_db`, and a
Groq API key in `.env` at the repo root (`GROQ_API_KEY=…`).

```bash
source .venv/bin/activate
pip install -r requirements.txt

# 1. Load data (creates/populates scriptly_db; edit DB credentials at the top of the script)
python load_to_mysql.py

# 2. Ingest speeches into ChromaDB with spaCy metadata (one-off)
python ingest_data.py

# Terminal 1 — backend on :8000 (start first, the frontend calls it)
cd backend && ../.venv/bin/python manage.py runserver

# Terminal 2 — static server for the frontend on :5500
cd frontend && ../.venv/bin/python -m http.server 5500
```

Open http://127.0.0.1:5500 in your browser.

## Further docs

- [schema.md](schema.md) — full table definitions, relationships, endpoint list
- [backend.md](backend.md) — backend setup and layout notes
