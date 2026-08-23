from rest_framework import generics

from .models import Play, Scene, Speech
from .serializers import PlaySerializer, SceneSerializer, SpeechSerializer


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
