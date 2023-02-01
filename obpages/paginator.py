import django.core.paginator


class MeiliPaginator(django.core.paginator.Paginator):
    """A paginator which constructs pages by executing search queries."""

    def __init__(
        self, queryset, index, query, opt_params, per_page, allow_empty_first_page=True
    ):
        self.queryset = queryset
        self.index = index
        self.query = query
        self.opt_params = opt_params
        self.per_page = int(per_page)
        self.orphans = 0
        self.allow_empty_first_page = allow_empty_first_page

    def page(self, number):
        """Return a Page object for the given 1-based page number."""
        number = self.validate_number(number)
        opt_params = self.opt_params.copy()
        opt_params.update(**{"page": number, "hitsPerPage": self.per_page})
        print(f"Executing search with query= {self.query}, params {opt_params}")
        results = self.index.search(self.query, opt_params)

        self.count = results["totalHits"]
        self.num_pages = results["totalPages"]

        result_pks = [hit["pk"] for hit in results["hits"]]
        object_list = sorted(
            self.queryset.filter(pk__in=result_pks),
            key=lambda x: result_pks.index(x.pk),
        )
        return self._get_page(object_list, number, self)

    def validate_number(self, number):
        """Validate the given 1-based page number."""
        try:
            if isinstance(number, float) and not number.is_integer():
                raise ValueError
            number = int(number)
        except (TypeError, ValueError):
            raise django.core.paginator.PageNotAnInteger(
                "Page number is not an integer"
            )
        if number < 1:
            raise django.core.paginator.EmptyPage("Page number is less than 1")
        # we can't check if the page number is too big because we don't know the number
        # of pages in advance
        return number
