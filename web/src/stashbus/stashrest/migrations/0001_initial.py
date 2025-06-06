# Generated by Django 5.2.1 on 2025-05-20 23:26

from typing import Any
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DataProducer",
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
                ("name", models.CharField(max_length=30)),
                (
                    "command",
                    models.CharField(
                        choices=[("PRODUCE", "Produce"), ("STOP", "Stop")],
                        default="PRODUCE",
                        max_length=7,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Secret",
            fields=[
                (
                    "name",
                    models.CharField(max_length=30, primary_key=True, serialize=False),
                ),
                ("value", models.TextField(max_length=2048)),
            ],
        ),
    ]
