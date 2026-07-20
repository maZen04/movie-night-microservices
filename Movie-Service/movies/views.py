from django.shortcuts import render
from rest_framework.views import APIView
from .services.movie_service import MovieService
from .services.tmdb_service import TMDBService
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .serializers import MovieSerializer, WatchlistSerializer, WatchedSerializer
from .models import Movie, Genre, MovieGenre, Watchlist, Watched
from types import NoneType
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from common.throttles import SearchThrottle, MovieDetailThrottle, RecommendationThrottle 
from django.db import transaction

class SearchView(APIView):
    throttle_classes = [SearchThrottle]

    def get(self, request):
        movie_name = request.query_params.get("query")
        page = request.query_params.get("page", 1)
        if type(movie_name) is not NoneType and movie_name.strip():
            api_call = MovieService()
            searched_movies =  api_call.search_movie(movie_name,page)
            if searched_movies:
                return Response(searched_movies)
            else:
                raise ValidationError({
                    "There're no movies found."
                })
        
        raise ValidationError({
                "query": ["query required for search."]
            })
    

class RecommendationView(APIView):
    throttle_classes = [RecommendationThrottle]

    def get(self, request, movie_id):
        if movie_id:
            api_call = MovieService()
            searched_movies =  api_call.get_movie_recommendations(movie_id)
            if searched_movies:
                return Response(searched_movies)
            else:
                raise ValidationError({
                        "There's no movies with this id."
                    })


class MovieDetailView(APIView):
    throttle_classes = [MovieDetailThrottle]

    def get(self, request, movie_id):
        if movie_id:
            movie_object = Movie.objects.prefetch_related("moviegenre_set__genre").filter(tmdb_id=movie_id).first()

            if movie_object:
                serializer = MovieSerializer(movie_object)
                return Response(serializer.data)
            
            else:
                api_call = TMDBService()
                movie_details = api_call.get_movie_details(movie_id)
                with transaction.atomic():
                    movie = Movie(
                        tmdb_id=movie_details["tmdb_id"],
                        title=movie_details["title"],
                        overview=movie_details["overview"],
                        poster_path=movie_details["poster_path"],
                        release_date=movie_details["release_date"],
                        runtime=movie_details["runtime"],
                        original_language=movie_details["original_language"],
                        vote_average=round(movie_details["vote_average"], 2),
                    )
                    movie.full_clean()
                    movie.save()

                    genre_ids = movie_details["genres"]
                    for genre_data in genre_ids:
                        genre, _ = Genre.objects.get_or_create(
                            tmdb_genre_id=genre_data["tmdb_genre_id"],
                            defaults={"tmdb_genre_id": genre_data["tmdb_genre_id"],"name": genre_data["name"]}
                        )

                        MovieGenre.objects.get_or_create(
                            movie=movie,
                            genre=genre
                        )

                serializer = MovieSerializer(movie)
                return Response(serializer.data)


class WatchlistView(generics.ListAPIView):
    serializer_class = WatchlistSerializer
    filter_backends = [DjangoFilterBackend]
    # filterset_fields = []
    
    def get_queryset(self):
        user_id = self.request.headers.get("X-User-ID")

        return (
            Watchlist.objects
            .filter(user_id=user_id)
            .select_related("movie")
            .order_by("-added_at")
        )

class WatchedHistoryView(generics.ListAPIView):
    serializer_class = WatchedSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['rating']

    def get_queryset(self):
        user_id = self.request.headers.get("X-User-ID")

        return (
            Watched.objects
            .filter(user_id=user_id)
            .select_related("movie")
            .order_by("-watched_at")
        )


class WatchlistEditView(APIView):
    def post(self, request, movie_id):
        if movie_id:
            user_id = request.headers.get("X-User-ID")
            if not user_id:
                raise ValidationError({
                    "user_id": ["User ID is required."]
                })
            
            movie = Movie.objects.filter(id=movie_id).first()
            if not movie:
                raise ValidationError({
                    "movie_id": ["Movie not found."]
                })
            
            watchlist, created = Watchlist.objects.get_or_create(
                movie = movie,
                user_id = user_id
            )

            if not created:
                raise ValidationError({
                    "movie": ["Movie already exists in watchlist."]
                })
            
            return Response({
                "message": "Movie added to watchlist successfully."
            }, status=201)
        
    def delete(self, request, movie_id):
        user_id = request.headers.get("X-User-ID")

        watchlist = Watchlist.objects.filter(
            id=movie_id,
            user_id=user_id
        ).first()

        if not watchlist:
            raise ValidationError({
                "movie": ["Movie is not in watchlist."]
            })

        watchlist.delete()

        return Response({
            "message": "Movie removed from watchlist successfully."
        })


class WatchedEditView(APIView):
    def post(self, request, movie_id):
        if movie_id:
            user_id = request.headers.get("X-User-ID")
            if not user_id:
                raise ValidationError({
                    "user_id": ["User ID is required."]
                })
            
            movie = Movie.objects.filter(id=movie_id).first()
            if not movie:
                raise ValidationError({
                    "movie_id": ["Movie not found."]
                })
            
            watchlist, created = Watched.objects.get_or_create(
                movie = movie,
                user_id = user_id,
                defaults={
                    "rating": request.data.get("rating")
                }
            )

            if not created:
                raise ValidationError({
                    "movie": ["Movie already you watched it."]
                })
            
            Watchlist.objects.filter(
                movie=movie,
                user_id=user_id
            ).delete()
            
            return Response({
                "message": "Movie added to Watched History successfully."
            }, status=status.HTTP_201_CREATED)

    def delete(self, request, movie_id):
        user_id = request.headers.get("X-User-ID")

        watchlist = Watchlist.objects.filter(
            id=movie_id,
            user_id=user_id
        ).first()

        if not watchlist:
            raise ValidationError({
                "movie": ["Movie is not in watchlist."]
            })

        watchlist.delete()

        return Response({
            "message": "Movie removed from watched history successfully."
        })