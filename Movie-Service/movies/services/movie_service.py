from django.core.cache import cache
from .tmdb_service import TMDBService


tmdb = TMDBService()

class MovieService:

    def search_movie(self, movie_name, page):
        key = f"search:{movie_name.lower().strip()}:{page}"

        movies = cache.get(key)

        if movies:
            print("From Cache")
            return movies
        
        print("From TMDB")
        movies = tmdb.search_movie(movie_name, page)
        cache.set(key, movies, 60*60*24)

        return movies
        
    def get_movie_recommendations(self, movie_id):
        key = f"recommend:{movie_id}"

        movies = cache.get(key)

        if movies:
            print("From Cache")
            return movies
        
        print("From TMDB")
        movies = tmdb.get_movie_recommendations(movie_id)
        cache.set(key, movies, 60*60*24)

        return movies