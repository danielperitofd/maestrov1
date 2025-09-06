from django.urls import path
from . import views

app_name = "musicas"

urlpatterns = [
    path("", views.song_list, name="song_list"),
    path("add/", views.song_create, name="song_create"),
    path("edit/<int:pk>/", views.song_edit, name="song_edit"),
    path("delete/<int:pk>/", views.song_delete, name="song_delete"),
    path("import/", views.song_import, name="song_import"),
    path("import-spotify/", views.import_from_spotify, name="import_from_spotify"),
    path("confirm-spotify-import/", views.confirm_spotify_import, name="confirm_spotify_import"),


]
