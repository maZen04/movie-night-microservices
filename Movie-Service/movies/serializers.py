from rest_framework import serializers
from .models import Movie, Watchlist, Watched, Genre

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["name"]


class MovieSerializer(serializers.ModelSerializer):
    genres = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = ['id', 'tmdb_id', 'title', 'overview', 'poster_path', 'release_date', 'runtime', 'original_language', 'vote_average', 'genres']

    def get_genres(self, obj):
        genres = Genre.objects.filter(moviegenre__movie=obj)
        return GenreSerializer(genres, many=True).data



class MovieCard(serializers.ModelSerializer):

    class Meta:
        model = Movie
        fields = ['title', 'overview', 'poster_path', 'release_date', 'vote_average']


class WatchlistSerializer(serializers.ModelSerializer):
    movie = MovieCard(read_only=True)

    class Meta:
        model = Watchlist
        fields = [
            "user_id",
            "movie",
            "added_at",
        ]


class WatchedSerializer(serializers.ModelSerializer):
    movie = MovieCard(read_only=True)

    class Meta:
        model = Watched
        fields = [
            "user_id",
            "movie",
            "watched_at",
            "rating"
        ]