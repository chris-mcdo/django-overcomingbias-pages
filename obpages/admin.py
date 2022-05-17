from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.core.management import call_command
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from elasticsearch import ElasticsearchException

from obpages.models import SearchIndex, User

admin.site.register(User, UserAdmin)


@admin.register(SearchIndex)
class SearchIndexAdmin(admin.ModelAdmin):
    manage_search_template = "admin/obpages/manage_search.html"

    def get_urls(self):
        return [
            path(
                "",
                self.admin_site.admin_view(self.manage_search_view),
                name="obpages_searchindex_changelist",
            )
        ]

    @method_decorator(csrf_protect)
    def manage_search_view(self, request):
        # (1) Check permissions
        if not self.has_module_permission(request):
            raise PermissionDenied

        # (2)
        opts = self.model._meta

        if request.method == "POST":
            # Configure action
            if "_update" in request.POST:
                required_permission = "obpages.update_search_index"
                action = "update_index"
                success_message = "Updated Index!"
            elif "_rebuild" in request.POST:
                required_permission = "obpages.rebuild_search_index"
                action = "rebuild_index"
                success_message = "Rebuilt Index!"
            else:
                raise SuspiciousOperation

            # Execute action
            if not request.user.has_perm(required_permission):
                raise PermissionDenied
            try:
                call_command(action, "--noinput")
            except ElasticsearchException as e:
                self.message_user(
                    request,
                    message="Elastic search exception %s" % e,
                    level=messages.ERROR,
                )
            else:
                self.message_user(
                    request, message=success_message, level=messages.SUCCESS
                )

        context = {
            **self.admin_site.each_context(request),
            "module_name": str(opts.verbose_name_plural),
            "title": "Search Index Management",
            "subtitle": None,
            "is_popup": False,
            "opts": opts,
        }

        request.current_app = self.admin_site.name

        # Prevent form resubmission if page is refreshed
        if request.method == "POST":
            return HttpResponseRedirect(request.get_full_path())

        return TemplateResponse(request, self.manage_search_template, context)
