import django.forms
from django.core.exceptions import ValidationError


class CustomModelMultipleChoiceField(django.forms.ModelMultipleChoiceField):
    """Model Multiple Choice Field which normalizes to a set of object names."""

    def clean(self, value):
        value = self.prepare_value(value)
        if self.required and not value:
            raise ValidationError(self.error_messages["required"], code="required")
        elif not self.required and not value:
            return set()
        if not isinstance(value, (list, tuple)):
            raise ValidationError(
                self.error_messages["invalid_list"],
                code="invalid_list",
            )
        pks = self._check_values(value)
        # Since this overrides the inherited ModelChoiceField.clean
        # we run custom validators here
        self.run_validators(value)
        return pks

    def _check_values(self, value):
        """
        Given a list of possible PK values, return a set of the
        corresponding object names. Raise a ValidationError if a given value is
        invalid (not a valid PK, not in the queryset, etc.)
        """
        key = self.to_field_name or "pk"
        # deduplicate given values to avoid creating many querysets or
        # requiring the database backend deduplicate efficiently.
        try:
            value = frozenset(value)
        except TypeError:
            # list of lists isn't hashable, for example
            raise ValidationError(
                self.error_messages["invalid_list"],
                code="invalid_list",
            )
        for pk in value:
            try:
                self.queryset.filter(**{key: pk})
            except (ValueError, TypeError):
                raise ValidationError(
                    self.error_messages["invalid_pk_value"],
                    code="invalid_pk_value",
                    params={"pk": pk},
                )
        qs = self.queryset.filter(**{"%s__in" % key: value})
        pks = {str(getattr(o, key)) for o in qs}
        for val in value:
            if str(val) not in pks:
                raise ValidationError(
                    self.error_messages["invalid_choice"],
                    code="invalid_choice",
                    params={"value": val},
                )
        values = {str(o) for o in qs}
        return values


class ClassifierMultipleChoiceField(CustomModelMultipleChoiceField):
    def __init__(self, model, **kwargs):
        kwargs.setdefault("required", False)
        kwargs.setdefault("to_field_name", "slug")
        kwargs.setdefault("label", model._meta.verbose_name_plural.title())
        super().__init__(queryset=model.objects.all(), **kwargs)


class SortOptionsField(django.forms.ChoiceField):
    """ChoiceField which normalizes data to a custom value."""

    def __init__(self, *, options=(), **kwargs):
        choices = [(value, names[0]) for value, names in options.items()]
        super().__init__(choices=choices, **kwargs)
        self.raw_names = {value: names[1] for value, names in options.items()}

    def clean(self, value):
        clean_data = super().clean(value)
        return self.raw_names.get(clean_data, "")
