import datetime

from obapi.models import (
    ContentItem,
    EssayContentItem,
    OBContentItem,
    SpotifyContentItem,
    YoutubeContentItem,
)

import obpages.utils

_PROTECTED_TYPES = (datetime.datetime, str, int, float, bool, type(None))


# Base serializer class ----------------------------------------------------------------
class MeiliSerializer:
    """Serialize a QuerySet of objects for indexing by MeiliSearch."""

    def __init__(self, model_fields, custom_fields=None):
        self.model_fields = model_fields
        self.custom_fields = custom_fields or {}

    def serialize(self, queryset):
        """Serialize a QuerySet of objects."""
        objects = []
        for obj in queryset:
            data = {"model": str(obj._meta), "pk": obj.pk}
            for field in self.model_fields:
                data[field.name] = self.serialize_field(obj, field)
            for target, field_map in self.custom_fields.items():
                field = field_map[0]
                mapper = field_map[1]
                data[target] = mapper(obj, field)
            objects.append(data)
        return objects

    def serialize_field(self, obj, field):
        """Handle serialization of a particular field."""
        if field.many_to_many:
            return self.handle_m2m_field(obj, field)
        elif field.many_to_one:
            return self.handle_fk_field(obj, field)
        else:
            return self.handle_normal_field(obj, field)

    def handle_normal_field(self, obj, field):
        encoders = {datetime.datetime: lambda x: int(datetime.datetime.timestamp(x))}
        value = field.value_from_object(obj)
        if not isinstance(value, _PROTECTED_TYPES):
            return field.value_to_string(obj)
        encode = encoders.get(type(value), lambda x: x)
        return encode(value)

    def handle_m2m_field(self, obj, field):
        return [str(related_obj) for related_obj in field.value_from_object(obj)]

    def handle_fk_field(self, obj, field):
        return str(getattr(obj, field.name, None))


# Custom handlers ----------------------------------------------------------------------
def handle_html(obj, field):
    return obpages.utils.html_to_plaintext(field.value_to_string(obj))


def get_content_type(obj, field):
    assert field is None
    return obj._meta.verbose_name_plural.title()


# Custom serializers -------------------------------------------------------------------
base_model_fields = [
    ContentItem._meta.get_field(field_name)
    for field_name in ("title", "publish_date", "authors", "topics", "ideas")
]
base_custom_fields = {"content_type": (None, get_content_type)}


CONTENT_SERIALIZERS = {
    OBContentItem: MeiliSerializer(
        base_model_fields,
        {
            **base_custom_fields,
            "text": (OBContentItem._meta.get_field("text_html"), handle_html),
        },
    ),
    EssayContentItem: MeiliSerializer(
        base_model_fields,
        {
            **base_custom_fields,
            "text": (EssayContentItem._meta.get_field("text_html"), handle_html),
        },
    ),
    SpotifyContentItem: MeiliSerializer(
        base_model_fields,
        {
            **base_custom_fields,
            "text": (
                SpotifyContentItem._meta.get_field("description_html"),
                handle_html,
            ),
        },
    ),
    YoutubeContentItem: MeiliSerializer(
        base_model_fields,
        {
            **base_custom_fields,
            "text": (
                YoutubeContentItem._meta.get_field("description_html"),
                handle_html,
            ),
        },
    ),
}


# Custom QuerySets ---------------------------------------------------------------------
CONTENT_QUERYSETS = {
    OBContentItem: OBContentItem.objects.only(
        "title", "publish_date", "text_html"
    ).prefetch_related("authors", "ideas", "topics"),
    EssayContentItem: EssayContentItem.objects.only(
        "title", "publish_date", "text_html"
    ).prefetch_related("authors", "ideas", "topics"),
    SpotifyContentItem: SpotifyContentItem.objects.only(
        "title", "publish_date", "description_html"
    ).prefetch_related("authors", "ideas", "topics"),
    YoutubeContentItem: YoutubeContentItem.objects.only(
        "title", "publish_date", "description_html"
    ).prefetch_related("authors", "ideas", "topics"),
}
