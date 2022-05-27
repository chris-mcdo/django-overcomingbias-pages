from django.core.management import call_command
from huey.contrib.djhuey import task


@task()
def update_search_index():
    action = "update_index"
    args = ["--remove"]
    call_command(action, *args)


@task()
def rebuild_search_index():
    action = "rebuild_index"
    args = ["--noinput"]
    call_command(action, *args)
