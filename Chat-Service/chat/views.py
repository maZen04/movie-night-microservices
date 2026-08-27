from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework import status

from .models import RecommendationSession
from .questions import QUESTIONS
from .serializers import (
    RecommendationSessionSerializer,
    AnswerSerializer,
)
from .services.llm_service import LLMService


class StartRecommendationView(APIView):

    def post(self, request):

        user_id = request.headers.get("X-User-ID")

        if not user_id:
            raise ValidationError({
                "user_id": ["User ID is required."]
            })

        session = RecommendationSession.objects.create(
            user_id=user_id
        )

        return Response({
            "session_id": session.id,
            "question": QUESTIONS[0],
        }, status=201)



class AnswerRecommendationView(APIView):

    def post(self, request, session_id):

        user_id = request.headers.get("X-User-ID")

        if not user_id:
            raise ValidationError({
                "user_id": ["User ID is required."]
            })

        session = RecommendationSession.objects.filter(
            id=session_id,
            user_id=user_id,
            status=RecommendationSession.Status.ACTIVE
        ).first()

        if not session:
            raise ValidationError({
                "session": ["Recommendation session not found."]
            })

        answer = request.data.get("answer")

        if not answer:
            raise ValidationError({
                "answer": ["Answer is required."]
            })

        # Get current question
        current_question = QUESTIONS[session.current_question]

        # Validate answer
        if answer not in current_question["options"]:
            raise ValidationError({
                "answer": ["Invalid answer for this question."]
            })

        # Save answer
        session.answers[current_question["id"]] = answer

        # Move to next question
        session.current_question += 1

        session.save(
            update_fields=[
                "answers",
                "current_question",
            ]
        )

        # Check if there are more questions
        if session.current_question < len(QUESTIONS):

            next_question = QUESTIONS[
                session.current_question
            ]

            return Response({
                "completed": False,
                "question": next_question,
            })

        # All questions answered
        return Response({
            "completed": True,
            "message": "All questions answered.",
            
        })


class CompleteRecommendationView(APIView):

    def post(self, request, session_id):

        user_id = request.headers.get("X-User-ID")

        if not user_id:
            raise ValidationError({
                "user_id": ["User ID is required."]
            })

        session = RecommendationSession.objects.filter(
            id=session_id,
            user_id=user_id,
            status=RecommendationSession.Status.ACTIVE
        ).first()

        if not session:
            raise ValidationError({
                "session": ["Recommendation session not found."]
            })

        if len(session.answers) != len(QUESTIONS):
            raise ValidationError({
                "answers": ["You must answer all questions first."]
            })

        try:
            llm_service = LLMService()

            recommendation = llm_service.recommend_movie(
                session.answers
            )

        except Exception as e:
            print("LLM ERROR:", repr(e))
            return Response({
                "status": "failed",
                "message": "Movie recommendation is temporarily unavailable."
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response({
            "status": "completed",
            "recommendation": recommendation,
        })