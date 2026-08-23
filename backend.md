# Scriptly Backend

Django + Django REST Framework API serving Shakespeare play data from MySQL.

## Stack

- Python (`.venv` virtual environment at repo root)
- Django / DRF
- MySQL database: `scriptly_db`

## Setup

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

Load the data first (creates and populates `scriptly_db`, see `schema.md`):

```bash
python load_to_mysql.py
```

## Running

All commands run from `backend/`:

```bash
cd backend
python manage.py check      # sanity check
python manage.py runserver  # dev server at http://127.0.0.1:8000/
```

## Project layout

- `backend/manage.py` — Django entrypoint
- `backend/scriptly_backend/` — project settings (`settings.py` holds DB config)
- `backend/scriptly_backend/cors.py` — simple CORS middleware so the frontend can call the API
- `backend/api/` — app with models, serializers, views, URL routes
- `frontend/` — vanilla HTML/CSS/JS reader app

## API endpoints

Base URL: `/api/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/plays/` | All plays (id, name), ordered by name |
| GET | `/api/plays/{play_id}/` | Single play detail |
| GET | `/api/plays/{play_id}/scenes/` | Scenes of a play, ordered by act/scene |
| GET | `/api/scenes/{scene_id}/speeches/` | Full script of a scene in order |
| GET | `/api/plays/{play_id}/characters/{name}/speeches/` | All lines of a character in a play |

Example:

```bash
curl http://127.0.0.1:8000/api/plays/
```

## Frontend

Vanilla HTML/CSS/JS app in `frontend/` (no build step). Run two terminals from the repo root:

```bash
# Terminal 1 — backend on :8000 (must be first, frontend calls it)
cd backend && ../.venv/bin/python manage.py runserver

# Terminal 2 — static server for the frontend on :5500
cd frontend && ../.venv/bin/python -m http.server 5500
```

Open http://127.0.0.1:5500 in your browser.

Features: play list with filter, act/scene navigation with prev/next buttons,
script reading view (speaker names + stage directions), search all lines by a
character within a play, dark/light theme toggle.

The API base URL is set to `http://127.0.0.1:8000/api` at the top of `frontend/app.js`.
