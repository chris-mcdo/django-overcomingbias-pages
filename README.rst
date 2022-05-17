django-overcomingbias-pages: web interface to Robin Hanson's content
====================================================================

``django-overcomingbias-pages`` is a standalone `Django <https://www.djangoproject.com/>`_
app which provides a web interface to Robin Hanson's content.

Features
--------

The main features are:

- Scrape content from across the web `overcomingbias <https://overcomingbias.com/>`_,
  `YouTube <https://www.youtube.com/>`_, `Spotify <https://spotify.com/>`_
  and more via the admin site.

- Search content using `elasticsearch <https://www.elastic.co/>`_
  or browse by topic.

- Create sequences (series) of content and export them to PDF, epub, plaintext,
  or any other format supported by `pandoc <https://pandoc.org/>`_.

- Persistent user accounts.

Configuration
-------------

To configure ``django-overcomingbias-pages``, add the following to your settings:

.. code-block:: python

  # add required apps
  INSTALLED_APPS = [
    # required for admin site / user accounts
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    # for collecting static files
    "django.contrib.staticfiles",
    # django-overcomingbias-api
    "ordered_model",
    "obapi",
    # haystack search
    "haystack",
    # django-overcomingbias-pages
    "obpages",
  ]

  # Use the (custom) obpages user model 
  AUTH_USER_MODEL = "obpages.User"


To configure search, follow the instructions on the
`django-haystack <https://django-haystack.readthedocs.io/en/master/>`_
doc pages.
If you don't care about search, just set up a dummy backend by adding this to your
settings:

.. code-block:: python

  # django-haystack dummy backend
  HAYSTACK_CONNECTIONS = {
    "default": {
      "ENGINE": "haystack.backends.simple_backend.SimpleEngine",
    },
  }


Bugs/Requests
-------------

Please use the
`GitHub issue tracker <https://github.com/chris-mcdo/django-overcomingbias-pages/issues>`_
to submit bugs or request features.

License
-------

Copyright (c) 2022 Christopher McDonald

Distributed under the terms of the
`MIT <https://github.com/chris-mcdo/django-overcomingbias-pages/blob/main/LICENSE>`_
license.

All overcomingbias posts are copyright the original authors.
