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
from .services.movie_service import MovieService


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
            print("STEP 1 - Calling LLM")
            llm_service = LLMService()

            recommendation = llm_service.recommend_movie(
                session.answers
            )

            print("STEP 2 - LLM response:", recommendation)

            movie_title = recommendation["movie_title"]

            print("STEP 3 - Searching:", movie_title)
            movie_service = MovieService()

            search_result = movie_service.search_movie(
                movie_title
            )

            print("STEP 4 - Search response:", search_result)

            results = search_result.get("results", [])

            if not results:
                return Response({
                    "status": "failed",
                    "message": "Could not find the recommended movie."
                }, status=status.HTTP_404_NOT_FOUND)

            movie_id = results[0]["id"]
            print("STEP 5 - Movie ID:", movie_id)
            movie = movie_service.get_movie_details(movie_id)
            print("STEP 6 - Movie details received")

        except Exception as e:
            import traceback

            print("RECOMMENDATION ERROR:", repr(e))
            traceback.print_exc()

            return Response({
                "status": "failed",
                "message": str(e),
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response({
            "status": "completed",
            "recommendation": recommendation,
            "movie":movie
        })