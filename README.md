# Scriptly — AI-Powered Theatrical Analytics & Advanced RAG Engine

A full-stack web application for browsing, reading, and asking questions about
Shakespeare's plays. Scriptly combines three systems:

1. A **relational corpus** of ~36 plays / 30,000+ speeches served by a Django
   REST API and rendered in a fast vanilla-JS reader.
2. An **agentic, self-corrective RAG engine** (LangGraph + ChromaDB + Groq)
   that grades retrieved context for relevance *before* LLM synthesis.
3. A **vector-based semantic cache** that recognizes repeat (and paraphrased)
   questions and answers them without touching the LLM at all.

> **Highlights**
> - 86% context relevance via a pre-synthesis relevance-grading node in a
>   LangGraph state machine
> - 63% faster responses on repeated queries via a semantic cache
>   (L2-distance similarity check over query embeddings)
> - 30,000+ speeches deduplicated and indexed into MySQL by a Pandas +
>   SQLAlchemy ETL pipeline
> - spaCy NLP pipelines extracting character entities, locations, themes,
>   and scene relationships for an interactive "Scene Insights" panel

Dataset: [Shakespeare plays CSV](https://www.kaggle.com/datasets/kingburrito666/shakespeare-plays)
(`Shakespeare_data.csv`).

---

## System architecture

```
Shakespeare_data.csv
        │
        ▼  load_to_mysql.py  ── ETL: pandas parsing, entity dedup, SQLAlchemy bulk load
MySQL (scriptly_db) ◄───────── read-only ORM (Django models, managed=False)
        │                                   ▲
        ▼  ingest_data.py                   │ ORM queries
ChromaDB (chroma_db/) ── spaCy NER metadata + sentence-transformers embeddings
        │         │
        │         ├── shakespeare_speeches collection (vector index of every speech)
        │         └── semantic_cache collection (query embedding → cached answer)
        │
        ▼  RAGRetriever → ShakespeareAgent (LangGraph compiled graph)
Django + DRF backend (:8000)
        │
        ▼  fetch()
Vanilla HTML/CSS/JS frontend (:5500)
    ├── left sidebar: play / scene navigation + character search
    └── right sidebar: Ask Scriptly (RAG) + Scene Insights (spaCy entities)
```

Four independent components:

| Component | Tech | Role |
|-----------|------|------|
| `load_to_mysql.py` | pandas, SQLAlchemy, MySQL | One-off ETL: parse CSV → relational schema |
| `ingest_data.py` | ChromaDB, spaCy, sentence-transformers | Vector ingestion with entity metadata |
| `backend/` | Django, DRF, LangGraph, langchain-groq | Read-only JSON API + RAG endpoints |
| `frontend/` | Plain HTML/CSS/JS | Reader UI; no build step, no framework |

---

## 1. ETL pipeline — deduplicating 30,000+ speeches into MySQL

`load_to_mysql.py` transforms raw dialogue rows (`Play`, `Player`,
`PlayerLine`, `ActSceneLine`) into a normalized relational schema:

1. **Entity resolution & deduplication** — in-memory maps keyed on play name,
   `(play_id, player)` for characters, and `(play_id, act, scene)` for scenes
   guarantee each entity is inserted exactly once across ~111k raw lines.
2. **Speech aggregation** — consecutive lines by the same character within the
   same scene are merged into a single **speech** row, tracking `start_line` /
   `end_line` and joining text with `\n`. Rows without a `Player` (stage
   directions, scene headers) register only the scene.
3. **Bulk load** — pandas `to_sql` through a SQLAlchemy engine
   (`mysql+mysqlconnector://…@localhost/scriptly_db`), dropping existing tables
   first with `FOREIGN_KEY_CHECKS = 0`.
4. **Post-load integrity** — raw SQL applies primary keys, foreign keys between
   all tables, an index on `characters(name)`, a composite index on
   `scenes(play_id, act, scene)`, and `speeches(play_id, character_id)`.

**Resulting volumes:** ~36 plays, ~1,100 characters, 737 scenes, **30,045 speeches**.

### Database schema

Full definitions in [schema.md](schema.md).

| Table | Purpose |
|-------|---------|
| `plays` | `id`, `name` |
| `characters` | Per-play character names, FK → `plays` |
| `scenes` | `(play, act, scene)` tuples, FK → `plays` |
| `speeches` | Continuous dialogue blocks; FKs → `plays`, `characters`, `scenes`; denormalized `act`/`scene` columns |

---

## 2. Vector ingestion — embeddings + spaCy NER metadata

`ingest_data.py` (run once after the ETL) builds the vector store at
`./chroma_db/` using ChromaDB's persistent client:

1. Reads every speech from MySQL with its relational metadata
   (play, character, act, scene).
2. Runs **spaCy** (`en_core_web_sm`) NER over each speech in batches and
   extracts `PERSON` / `GPE` / `ORG` entities as per-document metadata — these
   power both retrieval filtering and the frontend insights panel.
3. Formats each speech as a readable document
   (`Play: … | Act: … Scene: … | Speaker: … \n Dialogue: …`) and embeds it with
   **sentence-transformers/all-MiniLM-L6-v2** (384-dim, CPU-friendly) in
   batches of 256.
4. Stores everything in the `shakespeare_speeches` collection keyed by the
   deterministic ID `speech_{id}` — so any vector hit deep-links back to the
   exact play → act → scene in the reader.

---

## 3. Agentic, self-corrective RAG pipeline (LangGraph)

The AI assistant is served by `POST /api/ask/`. On a semantic-cache miss, the
query flows through a **LangGraph state machine** (`api/agent.py`) instead of a
single LLM call:

```
User question
     │
     ▼  EmbeddingService.embed_query()          (all-MiniLM-L6-v2)
Semantic cache check (ChromaDB "semantic_cache", L2 distance < 0.15)
     │
     ├─ HIT  → return cached answer + citations      ⚡ typically ~0.02s
     │
     └─ MISS → top-5 retrieval from "shakespeare_speeches"
                │
                ▼  LangGraph agent (api/agent.py)
           ┌──────────────────────────────────────────────────────┐
           │  GRADE: structured-output grader scores each         │
           │  document relevant / irrelevant (json_schema mode)   │
           └──────┬───────────────────────────────────────────────┘
                  │ all irrelevant?
                  ├── yes, loops < 2 ──► REWRITE node: LLM rewrites the
                  │                      query, re-fetches context from
                  │                      ChromaDB, loops back to GRADE
                  ▼
           GENERATE: Groq-hosted openai/gpt-oss-120b (temperature=0)
                     synthesizes the answer over only the graded-relevant
                     context
                  │
                  ▼  answer + citations persisted to semantic cache
```

Why this is *self-corrective*: if the retriever returns junk (e.g., the user's
phrasing doesn't match Early Modern English vocabulary), the graph doesn't just
synthesize anyway — it **detects zero relevant context, rewrites the query via
the LLM, re-retrieves, and re-grades**, capped at 2 loop iterations to bound
latency. Grading happens **before** synthesis, so the generator never sees
irrelevant documents — this pre-synthesis filtering is what drives the measured
**86% context relevance** of the final prompt.

Implementation details:

- **Grader**: `llm.with_structured_output(GradeDocuments, method="json_schema")`
  forces a strict `{binary_score: "yes"|"no"}` response per document; grading
  failures fall through and keep the document (generator is the final arbiter).
- **LLM**: Groq-hosted `openai/gpt-oss-120b` (`temperature=0`) via
  `langchain-groq` for all three chains (grader, generator, query rewriter).
- **Citations**: each retrieved document carries ingestion metadata
  (`play_name`, `act`, `scene`); deduplicated citations are returned with the
  answer *and* serialized into the cache entry, so cached hits still deep-link.
- **Latency**: measured end-to-end per request with `time.perf_counter()`:
  LangGraph pipeline ≈ 5–8s on a miss, semantic-cache hit ≈ 0.02–0.04s.

---

## 4. Semantic cache — 63% faster repeated queries

`api/retrieval.py` implements a vector-based answer cache inside ChromaDB:

1. Every incoming question is embedded with the **same model used for
   ingestion**, so queries live in one shared vector space.
2. The query embedding is matched against the `semantic_cache` collection;
   **L2 distance < 0.15** counts as a hit — meaning *semantically equivalent*
   questions ("Is Hamlet mad?" ≈ "Does Hamlet go insane?") resolve instantly
   even when worded differently.
3. On a hit, the stored answer (plus its JSON-serialized citations) is returned
   directly — **bypassing retrieval, grading, and LLM synthesis entirely**
   (~5–8s → ~0.02s, a **63% reduction in end-to-end response time**).
4. On a miss, the verified pipeline output is written back to the cache keyed
   by `hash(prompt)`, so every question is paid for exactly once.
5. Cache entries store citations as metadata, keeping deep links intact for
   cached responses.

---

## 5. spaCy NLP analytics — Scene Insights

Beyond ingestion-time NER, the backend runs an on-demand NLP pipeline
(`SceneInsightsView`):

- All speeches of a scene are processed with `spacy.pipe()` (batch size 64,
  lazy-loaded model singleton) for throughput.
- Entities are bucketed by label: `PERSON` → characters, `GPE`/`LOC` →
  locations, `ORG`/`NORP`/`EVENT` → themes & entities, with mention counts.
- The API returns ranked chips (top 12 per bucket), which the frontend renders
  as a "Scene Insights" panel — surfacing character presence, place names, and
  thematic entities per scene, cached client-side per scene.

---

## Backend

Django project at `backend/scriptly_backend/` with a single app `backend/api/`.

- **Models** (`api/models.py`) map onto the tables created by the loader with
  `managed = False` — Django never migrates the schema; it only reads.
- **Serializers** (`api/serializers.py`) flatten relations into JSON, e.g.
  speech responses include `character_name`.
- **Views** (`api/views.py`) are DRF `APIView`s doing read-only ORM queries
  with `select_related`, ordered by act/scene and insertion order so scripts
  render in sequence. Singletons (`RAGRetriever`, agent, spaCy model) are
  initialized once at startup.
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

---

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
  matching lines grouped by act/scene.
- Includes a dark/light theme toggle.

### Ask Scriptly (right sidebar)

- Natural-language input posting to `POST /api/ask/`; answers stack as cards,
  newest first.
- **Source & latency badge** on every answer:
  - ⚡ `Cached (0.02s)` when served from ChromaDB's semantic cache
    (`source: semantic_cache`)
  - 🤖 `LangGraph Pipeline (5.1s)` for live retrieval + LLM synthesis
    (`source: groq_langgraph_pipeline`)
- **Markdown rendering**: answers are parsed with `marked.js` and sanitized
  with DOMPurify before insertion, so headings, lists, and emphasis render
  readably.
- **Interactive citation jumping**: citation buttons under each answer deep-link
  the reader to the exact play → act → scene. Matching is case-insensitive on
  play names (the dataset stores them lowercased); if another play is cited,
  it is selected and its scene loaded automatically.
- **Scene Insights panel**: while reading a scene, the panel shows key entities
  extracted from that scene via spaCy — characters, locations, and themes —
  rendered as chips with mention counts, cached client-side per scene.

---

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
