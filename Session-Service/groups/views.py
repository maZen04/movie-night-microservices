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

        participant = SessionParticipant.objects.filter(user_id=user_id,session=session).first()
        if not participant:
            raise ValidationError({
                "user": ["You are not a member in this session."]
            })

        members = SessionParticipant.objects.filter(session=session)
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

        session.start()

        serializer = SessionSerializer(session)

        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            f"session_{session.id}",
            {
                "type": "session_started",
                "session_id": session.id,
            }
        )

        return Response({
            "message": "Session started successfully.",
            "data":serializer.data
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