from unittest.mock import patch

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, override_settings

from obpages.models import FeedbackNote, User
from obpages.views import FeedbackView


@pytest.mark.django_db
@pytest.mark.parametrize("authenticated", [False, True])
@pytest.mark.parametrize("feedback", [None, "", "   ", "Useful feedback"])
@override_settings(ROOT_URLCONF="obpages.urls")
def test_feedback_submission(authenticated, feedback):
    user = User.objects.create_user("visitor") if authenticated else AnonymousUser()
    data = {} if feedback is None else {"feedback": feedback}
    request = RequestFactory().post("/feedback", data)
    request.user = user

    with patch("obpages.views.USE_RECAPTCHA", False):
        response = FeedbackView.as_view()(request)

    if feedback == "Useful feedback":
        assert response.status_code == 302
        assert response.url == "/feedback/done"
        note = FeedbackNote.objects.get()
        assert note.feedback == feedback
        assert note.user_id == (user.pk if authenticated else None)
    else:
        assert response.status_code == 200
        form = response.context_data["form"]
        assert form.is_bound
        assert "feedback" in form.errors
        assert not FeedbackNote.objects.exists()


@pytest.mark.django_db
@override_settings(ROOT_URLCONF="obpages.urls")
def test_feedback_still_schedules_spam_check():
    request = RequestFactory().post(
        "/feedback", {"feedback": "Useful feedback", "g-recaptcha-response": "token"}
    )
    request.user = AnonymousUser()
    with patch("obpages.views.USE_RECAPTCHA", True), patch(
        "obpages.views.drop_feedback_if_spam", create=True
    ) as spam_check:
        response = FeedbackView.as_view()(request)
    assert response.status_code == 302
    spam_check.assert_called_once_with(FeedbackNote.objects.get().pk, "token")
