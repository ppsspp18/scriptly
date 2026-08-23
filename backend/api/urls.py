from django.urls import path

from .views import (
    CharacterSpeechListView,
    PlayDetailView,
    PlayListView,
    PlaySceneListView,
    SceneSpeechListView,
)

urlpatterns = [
    path('plays/', PlayListView.as_view(), name='play-list'),
    path('plays/<int:pk>/', PlayDetailView.as_view(), name='play-detail'),
    path('plays/<int:play_id>/scenes/', PlaySceneListView.as_view(), name='play-scenes'),
    path(
        'plays/<int:play_id>/characters/<str:character_name>/speeches/',
        CharacterSpeechListView.as_view(),
        name='character-speeches',
    ),
    path('scenes/<int:scene_id>/speeches/', SceneSpeechListView.as_view(), name='scene-speeches'),
]
