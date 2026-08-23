# Scriptly Database Schema

Source data: `Shakespeare_data.csv`, loaded into MySQL (`scriptly_db`) by `load_to_mysql.py`.
Each CSV row is a single line of dialogue; consecutive lines by the same character in the
same scene are merged into one **speech**.

## Tables

### plays
| Column | Type | Notes |
|--------|------|-------|
| id     | BIGINT PK | Auto-assigned (1..N) |
| name   | TEXT | Play title, e.g. "Henry IV" |

### characters
| Column    | Type | Notes |
|-----------|------|-------|
| id        | BIGINT PK | |
| play_id   | BIGINT FK → plays.id | Character names are per-play |
| name      | VARCHAR(255) | e.g. "KING HENRY IV". Indexed |

### scenes
| Column  | Type | Notes |
|---------|------|-------|
| id      | BIGINT PK | |
| play_id | BIGINT FK → plays.id | |
| act     | BIGINT | Parsed from `ActSceneLine` (act.scene.line) |
| scene   | BIGINT | Indexed: (play_id, act, scene) |

### speeches
A continuous block of text spoken by one character within one scene.

| Column       | Type | Notes |
|--------------|------|-------|
| id           | BIGINT PK | Insertion order = script order |
| play_id      | BIGINT FK → plays.id | |
| character_id | BIGINT FK → characters.id | Indexed with play_id |
| scene_id     | BIGINT FK → scenes.id | |
| act          | BIGINT | Denormalized from scenes |
| scene        | BIGINT | Denormalized from scenes |
| start_line   | BIGINT | First line number of the speech |
| end_line     | BIGINT | Last line number of the speech |
| text         | TEXT | Speech text; lines joined with `\n` |

## Relationships

- plays 1—N characters, scenes, speeches
- characters 1—N speeches
- scenes 1—N speeches

## API Endpoints

Base URL: `/api/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/plays/` | All plays (id, name), ordered by name |
| GET | `/api/plays/{play_id}/` | Single play detail |
| GET | `/api/plays/{play_id}/scenes/` | Scenes of a play (id, play, act, scene), ordered by act/scene |
| GET | `/api/scenes/{scene_id}/speeches/` | Full script of a scene in order (character_name included) |
| GET | `/api/plays/{play_id}/characters/{name}/speeches/` | All lines of a character in a play (case-insensitive name) |

Data volumes: ~36 plays, ~1,100 characters, 737 scenes, 30,045 speeches.
