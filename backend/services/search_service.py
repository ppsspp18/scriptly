from core.indexes import search_pool, play_name_by_id, characters_by_id


def search_speeches(query: str, play_id: int = None, character_id: int = None, limit: int = 20):
    query_lower = query.lower()
    results = []

    for entry in search_pool:
        if query_lower not in entry["text_lower"]:
            continue
        if play_id is not None and entry["play_id"] != play_id:
            continue
        if character_id is not None and entry["character_id"] != character_id:
            continue

        results.append({
            "speech_id": entry["speech_id"],
            "play_id": entry["play_id"],
            "play_name": play_name_by_id.get(entry["play_id"], "Unknown"),
            "character": characters_by_id.get(entry["character_id"], {}).get("name", "Unknown"),
            "act": entry["act"],
            "scene": entry["scene"],
            "snippet": _generate_snippet(entry["text"], query)
        })

        if len(results) >= limit:
            break

    return results


def _generate_snippet(text: str, query: str) -> str:
    idx = text.lower().find(query.lower())
    if idx == -1:
        return text[:200]
    start = max(0, idx - 60)
    end = min(len(text), idx + len(query) + 120)
    snippet = text[start:end].strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet
