# Generated by Django 4.0.4 on 2022-07-10 17:28

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("obpages", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="FeedbackNote",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "create_timestamp",
                    models.DateTimeField(
                        auto_now_add=True, help_text="When the note was created."
                    ),
                ),
                ("feedback", models.TextField()),
                (
                    "no_further_action",
                    models.BooleanField(
                        default=False,
                        help_text="Whether the feedback requires further action.",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        help_text="Which user the feedback belongs to.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="feedback_notes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
