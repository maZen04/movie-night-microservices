from django.shortcuts import render
from rest_framework.views import APIView
from .code import generate_session_code
from .serializers import *
from .models import *
from django.db import transaction
from rest_framework.response import Response
from rest_framework import generics
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .services.movie_service import MovieService
from .services.vote_store import VoteStorageService
import random


class CreateSessionView(APIView):

    @transaction.atomic
    def post(self, request):

        user_id = request.headers.get("X-User-ID")
        if not user_id:
            raise ValidationError({
                "user_id": ["User ID is required."]
            })
        
        session = Session.objects.create(
            code=generate_session_code()
        )
        SessionParticipant.objects.create(
            session=session,
            user_id=user_id,
            role=SessionParticipant.Role.LEADER
        )

        serializer = SessionSerializer(session)

        return Response(serializer.data, status=201)


class JoinSessionView(APIView):

    def post(self, request):
        user_id = request.headers.get("X-User-ID")
        code = request.data.get("code")
        if not user_id:
            raise ValidationError({
                "user_id": ["User ID is required."]
            })

        if not code:
            raise ValidationError({
                "code":["code is required"]
            })

        session = Session.objects.filter(code=code).first()
        if not session:
            raise ValidationError(
                {"This code is not valid."}
            )
        
        if session.status != Session.Status.WAITING:
            raise ValidationError({
                "session": ["You can't join this session now."]
            })
        
        if SessionParticipant.objects.filter(session=session, user_id=user_id).exists():
            raise ValidationError({
                "session": ["You are already in this session."]
            })

        
        
        SessionParticipant.objects.create(
            session=session,
            user_id=user_id,
            role=SessionParticipant.Role.MEMBER
        )

        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            f"session_{session.id}",
            {
                "type": "member_joined",
                "user_id": user_id,
            }
        )

        return Response({
            "message": "Joined session successfully."
        }, status=201)



class StartSessionView(APIView):

    def post(self, request, session_id):

        user_id = request.headers.get("X-User-ID")

        if not user_id:
            raise ValidationError({
                "user_id": ["User ID is required."]
            })

        session = Session.objects.filter(id=session_id).first()

        if not session:
            raise ValidationError({
                "session": ["There's no session with this id."]
            })

        participant = SessionParticipant.objects.filter(
            user_id=user_id,
            session=session
        ).first()

        if not participant:
            raise ValidationError({
                "user": ["You are not a member in this session."]
            })

        members = SessionParticipant.objects.filter(
            session=session
        )

        if members.count() < 2:
            raise ValidationError({
                "session": ["Members should be more than one."]
            })

        if participant.role == SessionParticipant.Role.MEMBER:
            raise ValidationError({
                "user": ["You should be a leader to start the session."]
            })

        if session.status != Session.Status.WAITING:
            raise ValidationError({
                "session": ["Session already started."]
            })

        # --------------------------------
        # Get participants
        # --------------------------------

        participant_ids = list(
            SessionParticipant.objects.filter(
                session=session
            ).values_list(
                "user_id",
                flat=True
            )
        )

        movie_service = MovieService()

        users_movies = {}
        movie_details = {}

        # --------------------------------
        # Get watchlists from Movie Service
        # --------------------------------

        for participant_id in participant_ids:

            watchlist = movie_service.get_user_watchlist(
                participant_id
            )

            users_movies[participant_id] = []

            for item in watchlist:

                movie = item["movie"]

                movie_id = movie["id"]

                # IDs used for voting
                users_movies[participant_id].append(
                    movie_id
                )

                # Data we will return to frontend
                movie_details[movie_id] = {
                    "id": movie_id,
                    "title": movie["title"],
                    "poster_path": movie["poster_path"],
                }

        # --------------------------------
        # Create union of all movies
        # --------------------------------

        all_movies = list({
            movie_id
            for movies in users_movies.values()
            for movie_id in movies
        })

        if not all_movies:
            raise ValidationError({
                "session": [
                    "Participants must have at least one movie in their watchlists."
                ]
            })

        # --------------------------------
        # Give every user the same movies
        # but in a different order
        # --------------------------------

        for participant_id in users_movies:

            users_movies[participant_id] = all_movies.copy()

            random.shuffle(
                users_movies[participant_id]
            )

        print("=" * 50)
        print("MOVIE DETAILS:")
        print(movie_details)

        print("=" * 50)
        print("FINAL USERS MOVIES:")
        print(users_movies)

        # --------------------------------
        # Start session
        # --------------------------------

        session.start()

        vote_storage = VoteStorageService()

        # Store shuffled movie IDs
        async_to_sync(
            vote_storage.initialize_session
        )(
            session.id,
            users_movies
        )

        # Store movie details
        async_to_sync(
            vote_storage.set_movie_details
        )(
            session.id,
            movie_details
        )

        # --------------------------------
        # Notify connected users
        # --------------------------------

        serializer = SessionSerializer(session)

        channel_layer = get_channel_layer()

        async_to_sync(
            channel_layer.group_send
        )(
            f"session_{session.id}",
            {
                "type": "session_started",
                "session_id": session.id,
            }
        )

        return Response({
            "message": "Session started successfully.",
            "data": serializer.data
        }, status=201)


class EndSessionView(APIView):
    
    def post(self, request, session_id):
            user_id = request.headers.get("X-User-ID")
            if not user_id:
                raise ValidationError({
                    "user_id": ["User ID is required."]
                })
    
            session = Session.objects.filter(id=session_id).first()
            if not session:
                raise ValidationError({
                    "session": ["There's no session with this id."]
                })
    
            participant = SessionParticipant.objects.filter(user_id=user_id,session=session).first()
            if not participant:
                raise ValidationError({
                    "user": ["You are not a member in this session."]
                })
    
            if participant.role == SessionParticipant.Role.MEMBER:
                raise ValidationError({
                    "user": ["You should be a leader to end the session."]
                })
    
            if session.status != Session.Status.ACTIVE:
                raise ValidationError({
                    "session": ["Session should start first."]
                })  
    
            movie_tmdb_id = request.data.get("movie_tmdb_id")

            if not movie_tmdb_id:
                raise ValidationError({
                    "movie_tmdb_id": ["This field is required."]
                })
            session.end(movie_tmdb_id)

            channel_layer = get_channel_layer()

            async_to_sync(channel_layer.group_send)(
                f"session_{session.id}",
                {
                    "type": "session_ended",
                    "movie_tmdb_id": movie_tmdb_id,
                }
            )
    
            serializer = SessionSerializer(session)
    
            return Response({
                "message": "Session ended successfully.",
                "data":serializer.data
            })


class SessionDetailView(generics.RetrieveAPIView):
    serializer_class = SessionSerializer
    lookup_url_kwarg = "session_id"

    def get_queryset(self):
        user_id = self.request.headers.get("X-User-ID")

        return (
            Session.objects
            .filter(participants__user_id=user_id)
            .prefetch_related("participants")
            .distinct()
        )