from django.db import models
from rest_framework.exceptions import ValidationError
from django.utils import timezone

class Session(models.Model):

    class Status(models.TextChoices):
        WAITING = "waiting", "Waiting"
        ACTIVE = "active", "Active"
        ENDED = "ended", "Ended"

    code = models.CharField(max_length=6, unique=True)
    movie_selected = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=7, choices=Status.choices, default=Status.WAITING)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"session {self.id}'s code is {self.code}"

    def start(self):
        if self.status != Session.Status.WAITING:
            raise ValidationError("Session already started.")

        self.status = Session.Status.ACTIVE
        self.started_at = timezone.now()
        self.save(update_fields=["status", "started_at"])


    def end(self, movie_tmdb_id):
        if self.status != Session.Status.ACTIVE:
            raise ValidationError("Session is not active.")

        self.status = Session.Status.ENDED
        self.movie_selected = movie_tmdb_id
        self.ended_at = timezone.now()

        self.save(update_fields=[
            "status",
            "movie_selected",
            "ended_at"
        ])


class SessionParticipant(models.Model):

    class Role(models.TextChoices):
        LEADER = "leader", "Leader"
        MEMBER = "member", "Member"

    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name="participants"
    )

    user_id = models.PositiveIntegerField(db_index=True)

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.MEMBER
    )

    class Meta: 
        constraints = [ 
            models.UniqueConstraint(
                fields=["session", "user_id"], 
                name="unique_session_user" 
            ) 
        ]

    def __str__(self):
        return f"{self.user_id} - {self.session.code}"