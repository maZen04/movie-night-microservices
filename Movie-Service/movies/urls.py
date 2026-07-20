from django.urls import path
from . import views

urlpatterns = [
    path('movies/search', views.SearchView.as_view(), name='search-movie'),
    path('movies/<int:movie_id>', views.MovieDetailView.as_view(), name='movie-details'),
    path('movies/<str:movie_id>/recommendations', views.RecommendationView.as_view(), name='recommend-movies'),
    path('movies/<int:movie_id>/watchlist', views.WatchlistEditView.as_view(), name='edit-watchlist'),
    path('movies/<int:movie_id>/watched', views.WatchedEditView.as_view(), name="edit-watched"),
    path('watchlist', views.WatchlistView.as_view(), name='watchlist'),
    path('watched', views.WatchedHistoryView.as_view(), name='watched'),
]