from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Movie(models.Model):
    tmdb_id = models.CharField(unique=True)
    title = models.CharField(max_length=255)
    overview = models.TextField()
    poster_path = models.CharField(max_length=255, null=True, blank=True)
    release_date = models.DateField(null=True, blank=True)
    runtime = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    original_language = models.CharField(max_length=10, null=True, blank=True)
    vote_average = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(10)])

    def __str__(self):
        return self.title
    

class Genre(models.Model):
    tmdb_genre_id = models.CharField(unique=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class MovieGenre(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["movie", "genre"],
                name="unique_movie_genre",
            )
        ]

    def __str__(self):
        return f"{self.movie.title} - {self.genre.name}"
    

class Watchlist(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    user_id = models.PositiveIntegerField(db_index=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["movie", "user_id"],
                name="unique_watchlist_movie_user",
            )
        ]

    def __str__(self):
        return f"{self.movie.title} - {self.user_id}"


class Watched(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    user_id = models.PositiveIntegerField(db_index=True)
    watched_at = models.DateTimeField(auto_now_add=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(10)])

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["movie", "user_id"],
                name="unique_watched_movie_user",
            )
        ]

    def __str__(self):
        return f"{self.movie.title} - {self.user_id}"