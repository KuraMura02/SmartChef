import uuid

from django.db import models


class SavedRecipe(models.Model):
    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    products = models.CharField(max_length=500)
    recipe = models.TextField()
    language = models.CharField(max_length=2, default="kk")
    minutes = models.PositiveSmallIntegerField(default=30)
    vegetarian = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.products


class RecipeVersion(models.Model):
    saved_recipe = models.ForeignKey(
        SavedRecipe,
        on_delete=models.CASCADE,
        related_name="versions",
    )
    recipe = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"Версия рецепта: {self.saved_recipe_id}, {self.created_at}"
