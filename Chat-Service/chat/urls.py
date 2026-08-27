from django.urls import path
from .views import (
    StartRecommendationView,
    AnswerRecommendationView,
    CompleteRecommendationView,
)

urlpatterns = [

    path(
        "recommendations/start",
        StartRecommendationView.as_view(),
        name="start-recommendation",
    ),

    path(
        "recommendations/<int:session_id>/answer",
        AnswerRecommendationView.as_view(),
        name="answer-recommendation",
    ),

    path(
        "recommendations/<int:session_id>/complete",
        CompleteRecommendationView.as_view(),
        name="complete-recommendation",
    ),

]