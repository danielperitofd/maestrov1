from django.urls import path, include
from django.contrib import admin
from . import views

app_name = "musicas"

urlpatterns = [
    path("repertorio/", views.song_repertorio, name="song_repertorio"),
    path("add/", views.song_create, name="song_create"),
    path("edit/<int:pk>/", views.song_edit, name="song_edit"),
    path("delete/<int:pk>/", views.song_delete, name="song_delete"),
    path("import/", views.song_import, name="song_import"),
    path("import-spotify/", views.import_from_spotify, name="import_from_spotify"),
    path("confirm-spotify-import/", views.confirm_spotify_import, name="confirm_spotify_import"),
    path("import-top-country/", views.import_top_country, name="import_top_country"),
    path("roadmap/", views.roadmap, name="roadmap"),
    path("bem-vindo/", views.welcome, name="welcome"),
    path("criar-organizacao/", views.create_company_and_band, name="create_company_and_band"),
    path("accounts/", include("allauth.urls")),
    path("admin/", admin.site.urls),
    path("perfil_membro/", views.perfil_membro, name="perfil_membro"), 
    path("config_system/", views.config_system, name="config_system"),
    path("cadastro-escolha/", views.register_choice, name="register_choice"),
    path("cadastro-manual/", views.register_manual, name="register_manual"),
    path("cadastro-equipe/", views.register_team_or_join, name="register_team_or_join"),


]
