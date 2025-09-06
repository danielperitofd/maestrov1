from django import forms
from .models import Song

class SongForm(forms.ModelForm):
    class Meta:
        model = Song
        fields = ["title", "artist", "key", "bpm", "lyrics_excerpt", "links", "category", "themes", "notes"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "input"}),
            "artist": forms.TextInput(attrs={"class": "input"}),
            "key": forms.TextInput(attrs={"class": "input"}),
            "bpm": forms.NumberInput(attrs={"class": "input"}),
            "lyrics_excerpt": forms.Textarea(attrs={"class": "textarea"}),
            "links": forms.Textarea(attrs={"class": "textarea"}),
            "themes": forms.TextInput(attrs={"class": "input"}),
            "notes": forms.Textarea(attrs={"class": "textarea"}),
        }
