from rest_framework import serializers
from .models import RecommendationSession


class RecommendationSessionSerializer(serializers.ModelSerializer):

    class Meta:
        model = RecommendationSession
        fields = [
            "id",
            "user_id",
            "current_question",
            "answers",
            "recommended_movie_id",
            "status",
            "created_at",
            "completed_at",
        ]
        read_only_fields = [
            "id",
            "user_id",
            "current_question"
            "recommended_movie_id",
            "status",
            "created_at",
            "completed_at",
        ]


class AnswerSerializer(serializers.Serializer):

    answer = serializers.CharField()