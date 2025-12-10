from django.conf import settings
from django.db import models


class UserViewInteraction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    show = models.ForeignKey("movies.MotnShow", on_delete=models.CASCADE)

    first_date = models.DateField(null=True, blank=True)
    last_date = models.DateField(null=True, blank=True)
    viewed_amount = models.SmallIntegerField(null=True, blank=True)
    completion_ratio = models.FloatField(null=True, blank=True)
    rating = models.IntegerField(default=0)

    class Meta:
        unique_together = ("user", "show")
        ordering = ["-last_date", "id"]

    def __str__(self):
        return f"{self.user_id}->{self.show}: first={self.first_date} rating={self.rating} viewed={self.viewed_amount}"


class UserRecommendation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recommendations")
    recommended_shows = models.JSONField(default=list)  # List of show IDs
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Recommendations for {self.user} (updated {self.updated_at})"


class UserQueryLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    query = models.TextField()
    top_k = models.IntegerField(default=50)
    
    # Store just the IDs of the results to save space, or a small JSON dump
    result_ids = models.JSONField(default=list)
    result_metadata_dump = models.JSONField(default=dict, blank=True, help_text="Search metadata like structured query")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        user_str = self.user.username if self.user else "Anonymous"
        return f"[{self.created_at}] {user_str}: {self.query[:50]}"
