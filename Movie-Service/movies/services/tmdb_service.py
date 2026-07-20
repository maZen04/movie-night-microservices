import requests
import os
from django.conf import settings
from dotenv import load_dotenv
import os
from datetime import datetime
from rest_framework.exceptions import ValidationError

load_dotenv()

# TMDB_BASE_URL = "https://api.themoviedb.org/3"
# TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
# API_KEY = os.getenv("TMDB_API_KEY")
# TMDB_READ_ACCESS_TOKEN = os.getenv("TMDB_READ_ACCESS_TOKEN")



class TMDBService:
    def __init__(self):
        self.api_key = os.getenv("TMDB_API_KEY")
        self.base_url = "https://api.themoviedb.org/3"
        self.image_base_url = "https://image.tmdb.org/t/p/w500"
        self.tmdb_read_access_token = os.getenv("TMDB_READ_ACCESS_TOKEN")

    def _get(self, endpoint, **params):
        params["api_key"] = self.api_key
        params["language"] = "en-US"
        response = requests.get(
            f"{self.base_url}/{endpoint}",
            params=params,
            timeout=10
        )
        # response.raise_for_status()

        if response.status_code == 404:
            raise ValidationError({
                "movie_id": ["Movie not found."]
            })

        return response.json()
    
    def _parse_date(self, date):
        if not date:
            return None

        return datetime.strptime(
            date,
            "%Y-%m-%d"
        ).date()
    
    def _build_image_url(self, path):

        if not path:
            return None

        return f"{self.image_base_url}{path}"
    
    def _movie_card(self, movie):
        return {
            "id": movie["id"],
            "title": movie["title"],
            "release_date": self._parse_date(movie.get("release_date")),
            "poster_path": self._build_image_url(movie.get("poster_path"))
        }
    
    def _movie_details(self, movie):
        return {
            "tmdb_id": movie["id"],
            "title": movie["title"],
            "overview": movie["overview"],
            "poster_path": self._build_image_url(movie.get("poster_path")),
            "release_date": self._parse_date(movie.get("release_date")),
            "runtime": int(movie["runtime"]) if movie.get("runtime") else None,
            "original_language": movie["original_language"],
            "vote_average": float(movie["vote_average"]) if movie.get("vote_average") else None,
            "genres": [{"tmdb_genre_id": genre["id"], "name": genre["name"]} for genre in movie.get("genres", [])]
        }

    def search_movie(self, movie_name, page=1):
        data = self._get("search/movie", query=movie_name, page=page)
        return {
            "page": data["page"],
            "total_pages": data["total_pages"],
            "total_results": data["total_results"],
            "results": [self._movie_card(movie) for movie in data["results"]]
        }

    def get_movie_details(self, movie_id):
        data = self._get(f"movie/{movie_id}")
        return self._movie_details(data)


    def get_movie_recommendations(self, movie_id):
        data = self._get(f"movie/{movie_id}/recommendations")
        return [self._movie_card(movie) for movie in data["results"]]

