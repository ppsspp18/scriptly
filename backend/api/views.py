from .agent import ShakespeareAgent
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
import time

import spacy

from .models import Play, Scene, Speech
from .serializers import PlaySerializer, SceneSerializer, SpeechSerializer
from .retrieval import RAGRetriever

# 1. Initialize the RAG Retriever once at startup
retriever = RAGRetriever()

class PlayListView(generics.ListAPIView):
    """Returns a list of all available plays."""
    queryset = Play.objects.all().order_by('name')
    serializer_class = PlaySerializer

class PlayDetailView(generics.RetrieveAPIView):
    """Returns details of a specific play."""
    queryset = Play.objects.all()
    serializer_class = PlaySerializer

class PlaySceneListView(generics.ListAPIView):
    """Returns all scenes for a specific play, ordered by act and scene."""
    serializer_class = SceneSerializer

    def get_queryset(self):
        play_id = self.kwargs['play_id']
        return Scene.objects.filter(play_id=play_id).order_by('act', 'scene')

class SceneSpeechListView(generics.ListAPIView):
    """Returns the script/speeches for a specific scene, in order."""
    serializer_class = SpeechSerializer

    def get_queryset(self):
        scene_id = self.kwargs['scene_id']
        # Ordering by 'id' preserves the sequential flow of the conversation
        return Speech.objects.filter(scene_ref_id=scene_id).select_related('character').order_by('id')

class CharacterSpeechListView(generics.ListAPIView):
    """Returns all speeches by a character within a play, in order."""
    serializer_class = SpeechSerializer

    def get_queryset(self):
        play_id = self.kwargs['play_id']
        character_name = self.kwargs['character_name']
        return (
            Speech.objects
            .filter(play_id=play_id, character__name__iexact=character_name)
            .select_related('character')
            .order_by('id')
        )

# --- RAG & Semantic Caching View ---

# Helper function allowing the agent to pull fresh data if it needs to rewrite a query
def fetch_more_context(query_string):
    query_vector = retriever.embedder.embed_query(query_string)
    results = retriever.collection.query(query_embeddings=[query_vector], n_results=5)
    return results["documents"][0]

# Initialize the LangGraph agent (Groq: openai/gpt-oss-20b)
agent = ShakespeareAgent(fetch_context_callback=fetch_more_context)

class AskShakespeareView(APIView):
    def post(self, request):
        start_time = time.perf_counter()
        user_query = request.data.get("query")
        
        if not user_query:
            return Response({"error": "Query is required"}, status=400)
            
        result = retriever.query(user_query)
        
        if result["cached"]:
            response_time = time.perf_counter() - start_time
            return Response({
                "answer": result["answer"],
                "source": "semantic_cache",
                "time_seconds": round(response_time, 4),
                "citations": result.get("citations", []),
            })
            
        # Trigger the Agentic LangGraph Pipeline
        try:
            final_answer = agent.answer(user_query, result['context'])
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        
        # Save the verified AI generation to the cache for future users
        retriever.save_to_cache(
            user_query, result["query_vector"], final_answer,
            citations=result.get("citations", []),
        )
        
        response_time = time.perf_counter() - start_time
        return Response({
            "answer": final_answer,
            "source": "groq_langgraph_pipeline",
            "time_seconds": round(response_time, 4),
            "citations": result.get("citations", []),
        })

# --- Entity & Character Insights Panel (spaCy metadata) ---

_nlp = None

def get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp

class SceneInsightsView(APIView):
    """Returns key extracted entities (characters, locations, themes) for a scene."""
    
    def get(self, request, scene_id):
        speeches = list(
            Speech.objects.filter(scene_ref_id=scene_id)
            .select_related('character')
            .order_by('id')
        )
        if not speeches:
            return Response({"characters": [], "locations": [], "themes": []})
        
        texts = [s.text or "" for s in speeches]
        docs = get_nlp().pipe(texts, batch_size=64)
        
        characters, locations, orgs = {}, {}, {}
        for doc in docs:
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    bucket = characters
                elif ent.label_ in ("GPE", "LOC"):
                    bucket = locations
                elif ent.label_ in ("ORG", "NORP", "EVENT"):
                    bucket = orgs
                else:
                    continue
                name = ent.text.strip()
                if len(name) < 3:
                    continue
                bucket[name] = bucket.get(name, 0) + 1
        
        def top(bucket, n=12):
            return [{"text": k, "count": v} for k, v in sorted(bucket.items(), key=lambda x: -x[1])[:n]]
        
        return Response({
            "characters": top(characters),
            "locations": top(locations),
            "themes": top(orgs),
        })
