# Generated by Django 4.1.4 on 2023-01-30 16:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("obpages", "0007_feedbacknote_spam_score"),
    ]

    operations = [
        migrations.DeleteModel(
            name="SearchIndex",
        ),
        migrations.CreateModel(
            name="SearchIndex",
            fields=[
                (
                    "index_uid",
                    models.SlugField(
                        help_text="Unique identifier for the index.",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "update_timestamp",
                    models.DateTimeField(
                        editable=False,
                        help_text="When the index was last updated.",
                        null=True,
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Search Indexes",
            },
        ),
    ]
