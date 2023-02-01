import functools
import logging

import django.conf
import django.utils.timezone
import meilisearch
import meilisearch.errors
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from obapi.modelfields import SimpleSlugField
from obapi.models import BaseSequence, BaseSequenceMember, ContentItem

import obpages.indexes
from obpages.utils import to_slug

logger = logging.getLogger(__name__)

USER_SLUG_MAX_LENGTH = 150


MEILISEARCH_INDEX_SETTINGS = {
    "filterableAttributes": ["authors", "topics", "ideas", "content_type"],
    "displayedAttributes": [
        "pk",
    ],
    "searchableAttributes": ["title", "ideas", "topics", "text"],
    "sortableAttributes": ["title", "publish_date"],
    "pagination": {"maxTotalHits": 10000},
}
MEILISEARCH_CLIENT = getattr(django.conf.settings, "MEILISEARCH_CLIENT", {})


class SearchIndex(models.Model):
    index_uid = models.SlugField(
        primary_key=True, help_text="Unique identifier for the index."
    )
    update_timestamp = models.DateTimeField(
        null=True, editable=False, help_text="When the index was last updated."
    )

    class Meta:
        verbose_name_plural = "Search Indexes"

    @functools.cached_property
    def _client(self):
        return meilisearch.Client(**MEILISEARCH_CLIENT)

    @functools.cached_property
    def _index(self):
        try:
            return self._client.get_index(self.index_uid)
        except meilisearch.errors.MeiliSearchCommunicationError:
            logger.warning(
                "Could not connect to MeiliSearch instance."
                " Using a dummy index instead."
            )
        except meilisearch.errors.MeiliSearchApiError:
            logger.warning(
                "Could not retrieve MeiliSearch index. Using a dummy index instead."
            )

        return obpages.indexes.DummyIndex()

    def delete(self, using=None, keep_parents=False):
        """Delete an index object and its associated Meili index.

        Gives a warning if the Meili index could not be deleted.
        """
        try:
            self.delete_meili_index()
        except meilisearch.errors.MeiliSearchError as exc:
            logger.warning(f"Could not delete MeiliSearch index. {exc.message}")
        finally:
            super().delete()

    def create_meili_index(self):
        # create index
        self.wait_for_task(
            self._client.create_index(self.index_uid, {"primaryKey": "pk"})["taskUid"]
        )
        # reset index cache
        self.__dict__.pop("_index", None)
        # configure index
        self.update_meili_settings(MEILISEARCH_INDEX_SETTINGS)

    def update_meili_settings(self, index_settings):
        self.wait_for_task(self._index.update_settings(index_settings)["taskUid"])

    def delete_meili_index(self):
        """Delete the meilisearch index.

        Raises an error if the index does not exist.
        """
        # delete index
        self.wait_for_task(self._index.delete()["taskUid"])
        # reset index cache
        self.__dict__.pop("_index", None)
        self.update_timestamp = None
        if self.pk and not self._state.adding:
            self.save(update_fields=["update_timestamp"])

    def search(self, query, opt_params):
        """Execute a search."""
        return self._index.search(query, opt_params)

    def update_meili_index(
        self, serializers, querysets=None, timestamp_field="update_timestamp"
    ):
        initial_timestamp = django.utils.timezone.now()
        for Model, serializer in serializers.items():
            queryset = querysets.get(Model, Model.objects.all())
            if self.update_timestamp:
                queryset = queryset.filter(
                    **{f"{timestamp_field}__gt": self.update_timestamp}
                )
            self.index_objects(serializer, queryset)
        self.update_timestamp = initial_timestamp
        self.save(update_fields=["update_timestamp"])

    def index_objects(self, serializer, queryset, chunk_size=1000):
        num_objects = queryset.count()
        for i in range(0, num_objects, chunk_size):
            objs = queryset[i : i + chunk_size]
            serialized_objs = serializer.serialize(objs)
            # Modified documents are fully replaced (rather than just updated)
            self.wait_for_task(self._index.add_documents(serialized_objs).task_uid)

    def wait_for_task(self, task_uid, timeout_in_ms=60e3, interval_in_ms=100):
        """Wait for a task to complete, and raise an error if it was unsuccessful.

        Allow a task 60 seconds to complete by default.
        """
        completed_task = self._client.wait_for_task(
            task_uid, timeout_in_ms=timeout_in_ms, interval_in_ms=interval_in_ms
        )
        task_status = completed_task["status"]
        if task_status != "succeeded":
            error = completed_task["error"]
            exc = meilisearch.errors.MeiliSearchError(error["message"])
            exc.code = error["code"]
            exc.link = error["link"]
            exc.type = error["type"]
            raise exc
        return completed_task

    def __str__(self):
        return self.index_uid


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


class UserSequence(BaseSequence):
    items = models.ManyToManyField(ContentItem, through="UserSequenceMember")

    owner = models.ForeignKey(
        django.conf.settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        editable=False,
        related_name="sequences",
    )
    public = models.BooleanField(
        default=False, help_text="Whether the sequence is public or private."
    )
    curated = models.BooleanField(
        default=False, help_text="Whether the sequence has been curated."
    )

    class Meta(BaseSequence.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "slug"], name="unique_usersequence_slug"
            )
        ]


class UserSequenceMember(BaseSequenceMember):
    sequence = models.ForeignKey(
        UserSequence,
        on_delete=models.CASCADE,
        related_name="members",
        related_query_name="members",
    )
    content_item = models.ForeignKey(
        ContentItem,
        on_delete=models.CASCADE,
        related_name="user_sequence_members",
        related_query_name="user_sequence_members",
    )


class FeedbackNote(models.Model):
    create_timestamp = models.DateTimeField(
        auto_now_add=True, help_text="When the note was created."
    )
    feedback = models.TextField()  # what the note says
    user = models.ForeignKey(
        django.conf.settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="feedback_notes",
        help_text="Which user the feedback belongs to.",
    )
    spam_score = models.FloatField(
        blank=True,
        null=True,
        help_text="How likely the note is spam. 0 means more likely, 1 means less.",
    )
    no_further_action = models.BooleanField(
        default=False, help_text="Whether the feedback requires further action."
    )

    def __str__(self):
        if self.user:
            username = self.user.username
        else:
            username = "Anonymous"
        return f"{username} - {self.create_timestamp:%a %d %b, %H:%M}"


class CuratedContentItem(models.Model):
    content_item = models.OneToOneField(
        "obapi.ContentItem",
        on_delete=models.CASCADE,
        primary_key=True,
        help_text="Which content item to curate",
    )

    def __str__(self):
        return f"{self.content_item}"
