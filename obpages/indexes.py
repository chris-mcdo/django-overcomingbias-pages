import math
import time

import django.apps
import django.conf

DUMMY_SEARCH_MODEL = getattr(
    django.conf.settings, "DUMMY_SEARCH_MODEL", "obapi.contentitem"
)
DUMMY_SEARCH_FIELD = getattr(
    django.conf.settings, "DUMMY_SEARCH_FIELD", "title__icontains"
)


class DummyIndex:
    """An index which executes search queries on the database.

    Raises a NotImplementedError when any other methods are used.
    """

    def __init__(
        self,
        search_model=DUMMY_SEARCH_MODEL,
        search_field=DUMMY_SEARCH_FIELD,
    ):
        self.search_model = django.apps.apps.get_model(search_model)
        self.search_field = search_field

    def update_settings(self, body):
        raise NotImplementedError

    def delete(self):
        raise NotImplementedError

    def search(self, query, opt_params=None):
        # read and validate parameters
        opt_params = opt_params or {}
        page = opt_params.get("page", 1)
        hits_per_page = opt_params.get("hitsPerPage", 10)
        if not isinstance(page, int) or page < 1:
            page = 1
        if not isinstance(hits_per_page, int) or hits_per_page < 1:
            hits_per_page = 10
        # for now, ignore optional parameters

        # set up query
        selection_start = hits_per_page * (page - 1)
        selection_end = hits_per_page * page

        # execute query
        counter_start = time.perf_counter()
        queryset = self.search_model.objects.filter(**{self.search_field: query}).only(
            "pk"
        )
        total_hits = queryset.count()
        results = list(queryset[selection_start:selection_end])
        counter_end = time.perf_counter()
        return {
            "hits": [{"pk": result.pk} for result in results],
            "query": query,
            "processingTimeMs": round((counter_end - counter_start) * 1000),
            "hitsPerPage": hits_per_page,
            "page": page,
            "totalPages": math.ceil(total_hits / hits_per_page),
            "totalHits": total_hits,
        }

    def add_documents(self, documents, primary_key):
        raise NotImplementedError
