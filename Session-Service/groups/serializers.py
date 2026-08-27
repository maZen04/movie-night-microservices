from rest_framework import serializers
from .models import Session, SessionParticipant

class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = '__all__'


class SessionParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionParticipant
        fields = [
            "user_id",
            "role",
        ]


class SessionDetailsSerializer(serializers.ModelSerializer):
    participants = SessionParticipantSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Session
        fields = [
            "code",
            "status",
            "created_at",
            "started_at",
            "ended_at",
            "participants",
        ]