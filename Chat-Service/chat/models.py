from django.db import models

class RecommendationSession(models.Model):

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    user_id = models.PositiveIntegerField(db_index=True)

    answers = models.JSONField(default=dict)

    current_question = models.PositiveIntegerField(default=0)

    recommended_movie_id = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    created_at = models.DateTimeField(auto_now_add=True)

    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )