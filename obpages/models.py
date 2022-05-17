from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from obapi.modelfields import SimpleSlugField

from obpages.utils import to_slug

USER_SLUG_MAX_LENGTH = 150


class User(AbstractUser):
    slug = SimpleSlugField(
        max_length=USER_SLUG_MAX_LENGTH,
        unique=True,
        editable=False,
    )

    def clean(self):
        # Set slug from username
        self.slug = to_slug(self.username, max_length=USER_SLUG_MAX_LENGTH)
        super().clean()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("user_detail", kwargs={"user_slug": self.slug})

    def __str__(self):
        return self.username


class SearchIndex(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ("update_search_index", "Can update the search index"),
            ("rebuild_search_index", "Can rebuild the search index"),
        )
        verbose_name_plural = "Search Indexes"
