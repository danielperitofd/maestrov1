from django.shortcuts import render, redirect, get_object_or_404
from .spotify_client import fetch_spotify_playlist, fetch_spotify_track, fetch_spotify_album
from .models import Category

from .models import Song
from .forms import SongForm
import csv
from django.contrib import messages

from .forms import CompanyForm, BandForm
from django.contrib.auth.decorators import login_required

@login_required
def create_company_and_band(request):
    if request.method == "POST":
        company_form = CompanyForm(request.POST)
        band_form = BandForm(request.POST)

        if company_form.is_valid() and band_form.is_valid():
            company = company_form.save()
            band = band_form.save(commit=False)
            band.company = company
            band.save()
            band.members.add(request.user)
            return redirect("musicas:welcome")  # ou outra página de boas-vindas
    else:
        company_form = CompanyForm()
        band_form = BandForm()

    return render(request, "musicas/create_company_and_band.html", {
        "company_form": company_form,
        "band_form": band_form
    })

@login_required
def welcome(request):
    user = request.user
    social = user.socialaccount_set.first()
    context = {
        "name": user.first_name or user.username,
        "email": user.email,
        "photo": social.extra_data.get("picture") if social else None,
        "social": social,
    }
    return render(request, "musicas/welcome.html", context)

def song_repertorio(request):
    songs = Song.objects.all()
    return render(request, "musicas/song_repertorio.html", {"songs": songs})

def song_create(request):
    if request.method == "POST":
        form = SongForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("musicas:song_repertorio")
    else:
        form = SongForm()
    return render(request, "musicas/song_form.html", {"form": form})

def song_edit(request, pk):
    song = get_object_or_404(Song, pk=pk)
    if request.method == "POST":
        form = SongForm(request.POST, instance=song)
        if form.is_valid():
            form.save()
            return redirect("musicas:song_repertorio")
    else:
        form = SongForm(instance=song)
    return render(request, "musicas/song_form.html", {"form": form})

def song_delete(request, pk):
    song = get_object_or_404(Song, pk=pk)
    song.delete()
    return redirect("musicas:song_repertorio")

# ------------ Modulo Import Musicas CSV -----------------------

def _try_read_csv_bytes(uploaded_file):
    """
    Tenta decodificar o arquivo em várias codificações comuns no BR.
    Retorna (texto_decodificado, encoding_usada) ou (None, None) se falhar.
    """
    encodings = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]
    for enc in encodings:
        try:
            uploaded_file.seek(0)
            return uploaded_file.read().decode(enc), enc
        except UnicodeDecodeError:
            continue
    return None, None

def _detect_dialect(sample_str):
    # Detecta delimitador ; ou ,. Se o Sniffer falhar, tenta fallback.
    try:
        return csv.Sniffer().sniff(sample_str, delimiters=";,")
    except Exception:
        class SimpleDialect(csv.Dialect):
            delimiter = ";" if ";" in sample_str.splitlines()[0] else ","
            quotechar = '"'
            doublequote = True
            skipinitialspace = True
            lineterminator = "\n"
            quoting = csv.QUOTE_MINIMAL
        return SimpleDialect()

def _normalize_keys(row):
    # Mapeia cabeçalhos PT->EN usados no modelo
    mapping = {
        "titulo": "title", "título": "title", "title": "title",
        "artista": "artist", "artist": "artist",
        "tom": "key", "key": "key",
        "bpm": "bpm",
        "letra": "lyrics_excerpt", "trecho": "lyrics_excerpt", "lyrics_excerpt": "lyrics_excerpt",
        "links": "links",
        "categoria": "category", "category": "category",
        "temas": "themes", "themes": "themes",
        "observacoes": "notes", "observações": "notes", "notes": "notes",
    }
    out = {}
    for k, v in row.items():
        if k is None:
            continue
        kk = mapping.get(k.strip().lower(), k.strip().lower())
        out[kk] = v
    return out

def _normalize_category(value):
    if not value:
        return "neutra"
    s = str(value).strip().lower()
    # tira acentos/variações simples
    for a, b in [("ç", "c"), ("ã", "a"), ("á","a"), ("â","a"),
                 ("é","e"), ("ê","e"), ("í","i"), ("ó","o"),
                 ("ô","o"), ("ú","u")]:
        s = s.replace(a, b)
    if "exalt" in s:
        return "exaltacao"
    if "ador" in s:
        return "adoracao"
    return "neutra"

def song_import(request):
    if request.method == "POST":
        csv_file = request.FILES.get("csv_file")
        if not csv_file:
            messages.error(request, "Selecione um arquivo CSV.")
            return redirect("musicas:song_repertorio")
        if not csv_file.name.lower().endswith(".csv"):
            messages.error(request, "Envie um arquivo .csv")
            return redirect("musicas:song_repertorio")

        text, used_enc = _try_read_csv_bytes(csv_file)
        if text is None:
            messages.error(request, "Não foi possível ler o CSV (encoding desconhecida). Tente salvar como 'CSV UTF-8' no Excel.")
            return redirect("musicas:song_repertorio")

        lines = text.splitlines()
        if not lines:
            messages.error(request, "O arquivo CSV está vazio.")
            return redirect("musicas:song_repertorio")

        created = 0
        skipped = 0  # <-- ESSA LINHA PRECISA ESTAR AQUI

        sample = lines[0]
        delimiter = ";" if sample.count(";") > sample.count(",") else ","
        reader = csv.DictReader(lines, delimiter=delimiter)
#--------------------------------------------------------------------------------------
        for raw in reader:
            row = _normalize_keys(raw)

            title = (row.get("title") or "").strip()
            if not title:
                skipped += 1
                continue

            artist = (row.get("artist") or "").strip() or None
            key = (row.get("key") or "").strip() or None
            bpm_raw = (row.get("bpm") or "").strip()
            try:
                bpm = int(bpm_raw) if bpm_raw else None
            except ValueError:
                bpm = None

            lyrics_excerpt = (row.get("lyrics_excerpt") or "").strip() or None
            links = (row.get("links") or "").strip() or None
            category = _normalize_category(row.get("category"))
            themes = (row.get("themes") or "").strip() or None
            notes = (row.get("notes") or "").strip() or None

            Song.objects.create(
                title=title, artist=artist, key=key, bpm=bpm,
                lyrics_excerpt=lyrics_excerpt, links=links,
                category=category, themes=themes, notes=notes
            )
            created += 1

        messages.success(request, f"Importadas {created} música(s). Ignoradas {skipped} linha(s) sem título. Encoding: {used_enc.upper()}.")
        return redirect("musicas:song_repertorio")

    return render(request, "musicas/song_import.html")

# -------------- SEÇÃO SPOTFY ------------------------

def import_from_spotify(request):
    if request.method == "POST":
        playlist_url = request.POST.get("playlist_url")
        if not playlist_url:
            messages.error(request, "Informe a URL da playlist do Spotify.")
            return redirect("musicas:import_from_spotify")

        try:
            if "playlist" in playlist_url:
                songs_data = fetch_spotify_playlist(playlist_url)
            elif "album" in playlist_url:
                songs_data = fetch_spotify_album(playlist_url)
            elif "track" in playlist_url:
                songs_data = fetch_spotify_track(playlist_url)
            else:
                messages.error(request, "URL inválida.")
                return redirect("musicas:import_from_spotify")
        except Exception as e:
            messages.error(request, f"Erro ao acessar Spotify: {e}")
            return redirect("musicas:import_from_spotify")

        categories = Category.objects.all()
        TONS = ["C", "Cm", "C#", "C#m", "D", "Dm", "D#", "D#m", "E", "Em", "F", "Fm", "F#", "F#m", "G", "Gm", "G#", "G#m", "A", "Am", "A#", "A#m", "B", "Bm"]
        return render(request, "musicas/spotify_preview.html", {
            "songs": songs_data,
            "categories": categories,
            "tones": TONS
        })

    return render(request, "musicas/import_spotify.html")


def confirm_spotify_import(request):
    if request.method == "POST":
        total = int(request.POST.get("total", 0))
        created = 0

        for i in range(1, total + 1):
            title = request.POST.get(f"title_{i}", "").strip()
            artist = request.POST.get(f"artist_{i}", "").strip()
            links = request.POST.get(f"links_{i}", "").strip()
            category = request.POST.get(f"category_{i}", "").strip()
            bpm_raw = request.POST.get(f"bpm_{i}", "").strip()
            key = request.POST.get(f"key_{i}", "").strip()

            try:
                bpm = int(bpm_raw) if bpm_raw else None
            except ValueError:
                bpm = None

            if not title or not artist:
                continue

            Song.objects.create(
                title=title,
                artist=artist,
                key=key or None,
                bpm=bpm,
                lyrics_excerpt="",
                links=links,
                category=category,
                themes="",
                notes=""
            )
            created += 1

        messages.success(request, f"{created} música(s) importadas da playlist.")
        return redirect("musicas:song_repertorio")
    
def import_top_country(request):
    band = request.user.userprofile.band  # ou country_code = "br" se ainda não tiver userprofile
    country_code = band.country

    top_playlists = {
        "br": "37i9dQZEVXbMXbN3EUUhlg",
        "us": "37i9dQZEVXbLRQDuF5jeBp",
        "pt": "37i9dQZEVXbKyJS56d1pgi",
        # outros países...
    }

    playlist_id = top_playlists.get(country_code)
    if not playlist_id:
        messages.error(request, "Não há playlist configurada para este país.")
        return redirect("musicas:song_repertorio")

    try:
        songs_data = fetch_spotify_playlist(f"https://open.spotify.com/playlist/{playlist_id}")
    except Exception as e:
        messages.error(request, f"Erro ao acessar Spotify: {e}")
        return redirect("musicas:song_repertorio")

    categories = Category.objects.all()
    TONS = ["C", "Cm", "C#", "C#m", "D", "Dm", "D#", "D#m", "E", "Em", "F", "Fm", "F#", "F#m", "G", "Gm", "G#", "G#m", "A", "Am", "A#", "A#m", "B", "Bm"]

    return render(request, "musicas/spotify_preview.html", {
        "songs": songs_data,
        "categories": categories,
        "tones": TONS
    })

def roadmap(request):
    progress_data = {
        "musicas": {
            "title": "🎵 Músicas",
            "percent": 60,
            "items": [
                ("CRUD completo de músicas", True),
                ("Campos: título, artista, tom, BPM, letra, links, categoria, temas, observações", True),
                ("Importação via CSV/TXT/Excel", True),
                ("Normalização/deduplicação automática", False),
                ("Classificação com IA (categoria + temas)", False),
                ("Integração com Spotify", True),
                ("Integração com YouTube", False),
                ("Integração com CifraClub", False),
            ]
        },
        "setlists": {
            "title": "📋 Setlists",
            "percent": 15,
            "items": [
                ("Criar e salvar setlists com datas/horários", False),
                ("Estrutura fixa por momento", False),
                ("Definir tom de execução", False),
                ("Associação de equipe escalada", False),
                ("Upload de setlist externa", False),
                ("Random inteligente com regras e botão “manter”", False),
            ]
        },
        "equipe": {
            "title": "👥 Equipes e Organizações",
            "percent": 10,
            "items": [
                ("Cadastro de organizações com nome, cidade e país", False),
                ("Cadastro de equipes vinculadas à organização", False),
                ("Usuário pode criar ou entrar em várias equipes", False),
                ("Solicitação de entrada em equipe com aprovação", False),
                ("Gerenciamento de membros da equipe", False),
                ("Filtragem de repertório por equipe", False),
                ("Mensagem inteligente ao importar Top 100 sem equipe", False),
            ]
        },
        "ia": {
            "title": "🤖 Inteligência Artificial",
            "percent": 0,
            "items": [
                ("Embeddings semânticos para sugestão por tema", False),
                ("Classificação automática por BPM/letra", False),
                ("Sugestão em tempo real de Pós-Mensagem", False),
                ("Explicação da sugestão (“match 0.82 com tema Graça”)", False),
            ]
        },
        "dashboard": {
            "title": "🎛️ Dashboard & Relatórios",
            "percent": 0,
            "items": [
                ("Ranking das músicas mais tocadas", False),
                ("Estatísticas: BPM médio, tonalidades, temas", False),
                ("Histórico de setlists", False),
                ("Histórico da equipe", False),
            ]
        },
        "culto": {
            "title": "🕹️ Modo Culto (dinâmico)",
            "percent": 0,
            "items": [
                ("Tela simplificada para uso ao vivo", False),
                ("Busca por temas em tempo real", False),
                ("Botão rápido “Sugerir Pós-Mensagem”", False),
                ("Ações rápidas: “Tocar agora”, “Projetar link”", False),
            ]
        },
        "infra": {
            "title": "🌐 Infraestrutura",
            "percent": 40,
            "items": [
                ("Banco de dados: Postgres (produção), SQLite (dev)", True),
                ("Hospedagem gratuita: Railway / Render / PythonAnywhere", False),
                ("Exportar setlists como playlist (Spotify/YouTube)", False),
                ("Exportar calendário (ICS)", False),
                ("Subdomínio gratuito para testes online", False),
            ]
        }
    }

    return render(request, "musicas/roadmap.html", {"progress_data": progress_data})