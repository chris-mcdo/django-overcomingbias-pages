django-overcomingbias-pages: a web interface to Robin Hanson's content
======================================================================

``django-overcomingbias-pages`` is a standalone `Django <https://www.djangoproject.com/>`_
app which provides a web interface to Robin Hanson's content.

Features
--------

The main features are:

- Scrape content from across the web (`overcomingbias <https://overcomingbias.com/>`_,
  `YouTube <https://www.youtube.com/>`_, `Spotify <https://spotify.com/>`_
  and more) via the admin site.

- Search content with `meilisearch <https://www.meilisearch.com/>`_.

- Create sequences (series) of content and export them to PDF, epub, plaintext,
  or any other format supported by `pandoc <https://pandoc.org/>`_.

- Persistent user accounts.

Configuration
-------------

To configure ``django-overcomingbias-pages``, add the following to your settings:

.. code-block:: python

  # settings.py

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
    # async tasks
    "huey.contrib.djhuey",
    # django-overcomingbias-pages
    "obpages",
    # custom form rendering
    "django.forms",
  ]

  # Use the (custom) obpages user model 
  AUTH_USER_MODEL = "obpages.User"


Search is provided using ``meilisearch``.
To configure search, first set up a MeiliSearch instance, and then set up the following
settings:

.. code-block:: python

  # settings.py

  MEILISEARCH_CLIENT = {
      "url": "http://127.0.0.1:7700",
  }
  MEILISEARCH_INDEX = "content"

``MEILISEARCH_CLIENT`` specifies the location of the MeiliSearch instance, while
``MEILISEARCH_INDEX`` controls which MeiliSearch index is used for search.
Indexes can be created, updated and deleted via the admin site.

``django-overcomingbias-pages`` uses `Huey <https://github.com/coleifer/huey>`_ to
run tasks asynchronously.
To enable this feature, follow the
`Django/Huey instructions <https://huey.readthedocs.io/en/latest/django.html>`_.
A minimal configuration is shown below:

.. code-block:: python

  # settings.py

  connection_pool = ConnectionPool(host="127.0.0.1", port=6379, db=0, max_connections=100)

  # See docs for full list of settings
  HUEY = {
      "huey_class": "huey.PriorityRedisHuey",
      "name": PROJECT_NAME,
      "connection": {
          "connection_pool": connection_pool,
          # see redis-py for more options
          # https://redis-py.readthedocs.io/en/latest/connections.html
          "read_timeout": 0,
      },
      "consumer": {
          "workers": 4,
          "worker_type": "thread",
      },
  }

(Note that this requires (1) a Redis server running on localhost:6379 and (2) installing
via ``pip install django-overcomingbias-pages[redis]``.)

Optionally, you can also configure Huey as your
`email backend <https://github.com/chris-mcdo/django-huey-email-backend>`_.

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
