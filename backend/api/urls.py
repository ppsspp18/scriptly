from django.urls import path

from .views import (
    AskShakespeareView,
    CharacterSpeechListView,
    PlayDetailView,
    PlayListView,
    PlaySceneListView,
    SceneInsightsView,
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
    path('scenes/<int:scene_id>/insights/', SceneInsightsView.as_view(), name='scene-insights'),
    path('ask/', AskShakespeareView.as_view(), name='ask-shakespeare'),
]