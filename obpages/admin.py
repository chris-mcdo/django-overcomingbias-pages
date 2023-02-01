import meilisearch.errors
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.utils.text import Truncator
from obapi.admin import OBContentItemAdmin
from obapi.models import OBContentItem
from ordered_model.admin import OrderedInlineModelAdminMixin, OrderedTabularInline

import obpages.tasks
from obpages.models import (
    CuratedContentItem,
    FeedbackNote,
    SearchIndex,
    User,
    UserSequence,
    UserSequenceMember,
)

admin.site.register(User, UserAdmin)


class SpamScoreListFilter(admin.SimpleListFilter):
    title = "spam score"
    parameter_name = "spam_score"

    def lookups(self, request, model_admin):
        return (
            ("gt80", ">0.8"),
            ("gt50", ">0.5"),
            ("le50", "<=0.5"),
            ("none", "No Score"),
        )

    def queryset(self, request, queryset):
        if self.value() == "gt80":
            return queryset.filter(spam_score__gt=0.8)
        if self.value() == "gt50":
            return queryset.filter(spam_score__gt=0.5)
        if self.value() == "lte50":
            return queryset.filter(spam_score__lte=0.5)
        if self.value() == "none":
            return queryset.filter(spam_score=None)


@admin.register(FeedbackNote)
class FeedbackNoteAdmin(admin.ModelAdmin):
    readonly_fields = ("create_timestamp",)
    list_display = (
        "__str__",
        "create_timestamp",
        "no_further_action",
        "spam_score",
        "truncated_text",
    )
    list_filter = (
        "no_further_action",
        SpamScoreListFilter,
        ("user", admin.EmptyFieldListFilter),
    )

    @admin.display(description="Text")
    def truncated_text(self, obj):
        return Truncator(obj.feedback).chars(num=50, truncate="...")


@admin.register(SearchIndex)
class SearchIndexAdmin(admin.ModelAdmin):

    list_display = ("index_uid", "update_timestamp")
    actions = ["create_index", "delete_index", "update_index"]

    @admin.action(
        permissions=["change"],
        description="Create MeiliSearch index for selected indexes",
    )
    def create_index(self, request, queryset):
        for index in queryset:
            try:
                index.create_meili_index()
            except meilisearch.errors.MeiliSearchError as exc:
                self.message_user(
                    request,
                    f'Error creating "{index.index_uid}". {exc.message}',
                    messages.ERROR,
                )
            else:
                self.message_user(
                    request,
                    f'Successfully created Meili index "{index.index_uid}".',
                    messages.SUCCESS,
                )

    @admin.action(
        permissions=["change"],
        description="Delete MeiliSearch index for selected indexes",
    )
    def delete_index(self, request, queryset):
        for index in queryset:
            try:
                index.delete_meili_index()
            except meilisearch.errors.MeiliSearchError as exc:
                self.message_user(
                    request,
                    f'Error deleting "{index.index_uid}". {exc.message}',
                    messages.ERROR,
                )
            else:
                self.message_user(
                    request,
                    f'Successfully deleted Meili index "{index.index_uid}".',
                    messages.SUCCESS,
                )

    @admin.action(
        permissions=["change"],
        description="Update indexes with new / modified documents",
    )
    def update_index(self, request, queryset):
        for index in queryset:
            try:
                obpages.tasks.update_search_index(index.pk)
            except meilisearch.errors.MeiliSearchError as exc:
                self.message_user(
                    request,
                    f'Error updating Meili index "{index.index_uid}". {exc.message}',
                    messages.ERROR,
                )
            else:
                self.message_user(
                    request,
                    f'Attempting to update Meili index "{index.index_uid}".',
                    messages.INFO,
                )


class UserSequenceMemberInline(OrderedTabularInline):
    model = UserSequenceMember
    fields = (
        "content_item",
        "order",
        "move_up_down_links",
    )
    readonly_fields = (
        "order",
        "move_up_down_links",
    )
    ordering = ("order",)
    extra = 1
    autocomplete_fields = ("content_item",)


@admin.register(UserSequence)
class UserSequenceAdmin(OrderedInlineModelAdminMixin, admin.ModelAdmin):
    model = UserSequence
    list_display = ("title",)
    inlines = (UserSequenceMemberInline,)
    readonly_fields = ("create_timestamp", "update_timestamp")


@admin.register(CuratedContentItem)
class CuratedContentItemAdmin(admin.ModelAdmin):
    model = CuratedContentItem
    autocomplete_fields = ("content_item",)


# Override obapi content item admin
admin.site.unregister(OBContentItem)


@admin.register(OBContentItem)
class CustomOBContentItemAdmin(OBContentItemAdmin):
    """OBContentItemAdmin which uses Huey to pull and sync posts asynchronously."""

    def pull(self, request):
        # Dispatch task
        obpages.tasks.download_new_items()
        # Message user
        self.message_user(
            request=request,
            message="Downloading new posts. Please wait up to 30 minutes.",
            level=messages.INFO,
        )

    def sync(self, request):
        # Dispatch task
        obpages.tasks.update_edited_items(user_pk=request.user.pk)
        # Message user
        self.message_user(
            request=request,
            message="Updating existing posts. Please wait a few minutes.",
            level=messages.INFO,
        )
