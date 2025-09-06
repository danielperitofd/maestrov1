from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path("admin/", admin.site.urls),
    path("musicas/", include("musicas.urls")),
    path("", lambda request: redirect("musicas:song_list")),  # redireciona raiz para músicas
]
