# Generated by Django 4.0.4 on 2022-07-11 11:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("obpages", "0004_usersequence_curated"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="usersequence",
            options={"ordering": ("-update_timestamp",)},
        ),
    ]