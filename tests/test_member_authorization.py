import datetime

import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from django.test import RequestFactory, override_settings
from django.urls import resolve, reverse
from obapi.models import EssayContentItem

from obpages.models import User, UserSequence, UserSequenceMember


@pytest.mark.django_db
@pytest.mark.parametrize("public", [False, True])
@pytest.mark.parametrize("operation", ["delete", "move"])
@pytest.mark.parametrize("identity", ["anonymous", "other", "owner"])
@override_settings(
    ROOT_URLCONF="obpages.urls",
    LOGIN_URL="/account/login",
    ALLOWED_HOSTS=["testserver"],
)
def test_member_mutation_requires_owner(public, operation, identity):
    owner = User.objects.create_user("owner")
    other = User.objects.create_user("other")
    sequence = UserSequence.objects.create(owner=owner, title="Sequence", public=public)
    members = []
    for i in range(3):
        item = EssayContentItem.objects.create(
            title=f"Essay {i}", item_id=f"essay-{i}",
            publish_date=datetime.datetime.now(datetime.timezone.utc),
        )
        members.append(UserSequenceMember.objects.create(sequence=sequence, content_item=item))
    target = members[1]
    before = list(sequence.members.order_by("order").values_list("pk", "order"))
    url = reverse(f"sequencemember_{operation}", kwargs={
        "user_slug": owner.slug, "sequence_slug": sequence.slug, "order": target.order,
    })
    request = RequestFactory().post(url, {"move": "top"})
    request.user = {"anonymous": AnonymousUser(), "other": other, "owner": owner}[identity]
    match = resolve(url)
    response = match.func(request, *match.args, **match.kwargs) if identity != "other" else None
    if identity == "other":
        with pytest.raises(Http404):
            match.func(request, *match.args, **match.kwargs)
    elif identity == "anonymous":
        assert response.status_code == 302
        assert response.url.startswith("/account/login?next=")
    else:
        assert response.status_code == 302
        if operation == "delete":
            assert not UserSequenceMember.objects.filter(pk=target.pk).exists()
        else:
            target.refresh_from_db()
            assert target.order == 0
    if identity != "owner":
        assert list(sequence.members.order_by("order").values_list("pk", "order")) == before
