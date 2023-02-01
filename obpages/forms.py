import django.forms
import django_select2.forms
import obapi.formfields
from django.utils.html import format_html
from obapi.models import (
    Author,
    EssayContentItem,
    Idea,
    OBContentItem,
    SpotifyContentItem,
    Topic,
    YoutubeContentItem,
)

import obpages.fields
import obpages.utils
from obpages.models import UserSequence, UserSequenceMember


def render_js(self):
    return [
        format_html('<script src="{}" defer></script>', self.absolute_path(path))
        for path in self._js
    ]


django.forms.widgets.Media.render_js = render_js

SORT_OPTIONS = {
    "relevance": ("Relevance", None),
    "alphabetical": ("Title", "title:asc"),
    "newest": ("Newest First", "publish_date:desc"),
    "oldest": ("Oldest First", "publish_date:asc"),
}

MODEL_SEARCH_CHOICES = [
    (model._meta.verbose_name_plural.title(), model._meta.verbose_name_plural.title())
    for model in (
        EssayContentItem,
        SpotifyContentItem,
        YoutubeContentItem,
        OBContentItem,
    )
]


class ContentSearchForm(django.forms.Form):
    query = django.forms.CharField(
        required=False,
        label="Search",
        widget=django.forms.HiddenInput,
    )

    sort = obpages.fields.SortOptionsField(
        options=SORT_OPTIONS,
        required=False,
        label="Sort By",
        widget=django.forms.Select(attrs={"onchange": "this.form.submit()"}),
    )
    authors = obpages.fields.ClassifierMultipleChoiceField(
        Author, widget=django_select2.forms.Select2MultipleWidget
    )
    ideas = obpages.fields.ClassifierMultipleChoiceField(
        Idea, widget=django_select2.forms.Select2MultipleWidget
    )
    topics = obpages.fields.ClassifierMultipleChoiceField(
        Topic, widget=django_select2.forms.Select2MultipleWidget
    )
    content_type = django.forms.MultipleChoiceField(
        choices=MODEL_SEARCH_CHOICES,
        required=False,
        widget=django_select2.forms.Select2MultipleWidget,
        label="Content Type",
    )

    def get_query(self):

        query = self.cleaned_data.get("query")
        opt_params = {}

        def add_filter(orig_params, filter_name, filter_values):
            orig_filters = orig_params.get("filter", [])
            new_filters = [
                f"{filter_name} = '{obpages.utils.escape_single_quotes(value)}'"
                for value in filter_values
            ]
            return orig_filters + [new_filters]

        if order_field := self.cleaned_data.get("sort"):
            opt_params["sort"] = [order_field]
        elif not query:
            opt_params["sort"] = [SORT_OPTIONS["newest"][1]]

        for filter_name in ["authors", "ideas", "topics", "content_type"]:
            if filter_values := self.cleaned_data.get(filter_name):
                opt_params["filter"] = add_filter(
                    opt_params, filter_name, filter_values
                )

        return query, opt_params


class SequenceExportForm(django.forms.Form):
    writer = obapi.formfields.PandocWriterField(label="Export To", initial="epub")


class SequenceChangeForm(django.forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["abstract"].widget.attrs.pop("cols")

    class Meta:
        model = UserSequence
        fields = ("title", "abstract", "public")

    def _get_validation_exclusions(self):
        exclude = super()._get_validation_exclusions()
        exclude.remove("owner")
        exclude.remove("slug")
        return exclude


class SequenceMemberMoveForm(django.forms.Form):
    SEQUENCEMEMBER_MOVE_CHOICES = [
        ("top", "Top"),
        ("up", "Up"),
        ("down", "Down"),
        ("bottom", "Bottom"),
    ]

    move = django.forms.ChoiceField(choices=SEQUENCEMEMBER_MOVE_CHOICES)


class UserSequenceMemberAddForm(django.forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sequence"].queryset = user.sequences.all()

    class Meta:
        model = UserSequenceMember
        fields = ("sequence",)
