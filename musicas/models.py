from django.db import models

class Song(models.Model):
    class Category(models.TextChoices):
        EXALTACAO = "exaltacao", "Exaltação"
        ADORACAO = "adoracao", "Adoração"
        NEUTRA = "neutra", "Neutra"

    title = models.CharField(max_length=200)
    artist = models.CharField(max_length=120, blank=True, null=True)
    key = models.CharField(max_length=10, blank=True, null=True)  # tom original
    bpm = models.PositiveIntegerField(blank=True, null=True)
    lyrics_excerpt = models.TextField(blank=True, null=True)  # trecho ou letra
    links = models.TextField(blank=True, null=True)  # links separados por vírgula
    category = models.CharField(
        max_length=20, choices=Category.choices, default=Category.NEUTRA
    )
    themes = models.CharField(max_length=200, blank=True, null=True)  # ex: Graça, Páscoa
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} ({self.artist})"

class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
