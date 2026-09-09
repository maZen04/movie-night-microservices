import requests
from django.conf import settings


class MovieService:

    def search_movie(self, movie_title):
        response = requests.get(
            f"{settings.MOVIE_SERVICE_URL}/api/movies/search",
            params={
                "query": movie_title
            },
            timeout=5
        )

        response.raise_for_status()

        return response.json()


    def get_movie_details(self, movie_id):
        response = requests.get(
            f"{settings.MOVIE_SERVICE_URL}/api/movies/{movie_id}",
            timeout=5
        )

        response.raise_for_status()

        return response.json()