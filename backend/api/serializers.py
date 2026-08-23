from rest_framework import serializers

from .models import Play, Scene, Speech


class PlaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Play
        fields = ['id', 'name']


class SceneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scene
        fields = ['id', 'play', 'act', 'scene']


class SpeechSerializer(serializers.ModelSerializer):
    # Fetch the character's string name rather than just the ID
    character_name = serializers.CharField(source='character.name', read_only=True)

    class Meta:
        model = Speech
        fields = ['id', 'act', 'scene', 'start_line', 'end_line', 'text', 'character_name']
