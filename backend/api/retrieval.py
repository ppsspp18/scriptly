import chromadb
from api.embeddings import EmbeddingService

class RAGRetriever:
    def __init__(self):
        self.embedder = EmbeddingService()
        # Path assumes execution from the root scriptly/ directory where manage.py lives
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        
        self.collection = self.chroma_client.get_collection("shakespeare_speeches")
        self.cache = self.chroma_client.get_or_create_collection("semantic_cache")

    def query(self, user_prompt: str):
        query_vector = self.embedder.embed_query(user_prompt)
        
        # 1. Check Semantic Cache
        cache_results = self.cache.query(query_embeddings=[query_vector], n_results=1)
        
        # L2 Distance < 0.15 indicates high semantic similarity (a cache hit)
        if cache_results["distances"][0] and cache_results["distances"][0][0] < 0.15:
            meta = (cache_results.get("metadatas") or [[None]])[0][0] or {}
            raw = meta.get("citations")
            try:
                import json
                citations = json.loads(raw) if raw else []
            except Exception:
                citations = []
            return {"cached": True, "answer": cache_results["documents"][0][0], "citations": citations}

        # 2. Cache MISS: Retrieve context from the main database
        results = self.collection.query(query_embeddings=[query_vector], n_results=5)
        context = [doc for doc in results["documents"][0]]

        # Build deep-linkable citations from ingestion metadata (play, act, scene)
        seen = set()
        citations = []
        for m in results["metadatas"][0]:
            key = (m.get("play_name"), m.get("act"), m.get("scene"))
            if key in seen:
                continue
            seen.add(key)
            citations.append({
                "play_name": m.get("play_name"),
                "act": int(m.get("act", 0)),
                "scene": int(m.get("scene", 0)),
            })

        return {"cached": False, "context": context, "citations": citations, "query_vector": query_vector}

    def save_to_cache(self, user_prompt: str, query_vector: list, answer: str, citations=None):
        # Hash the prompt for a unique ID; store citations so cache hits keep deep links
        import json
        self.cache.add(
            ids=[str(hash(user_prompt))],
            embeddings=[query_vector],
            documents=[answer],
            metadatas=[{"citations": json.dumps(citations or [])}],
        )