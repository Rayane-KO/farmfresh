# Generated by Django 4.1 on 2023-11-23 16:27

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("reviews", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="productreview",
            name="rating",
            field=models.IntegerField(
                choices=[(0, "0"), (1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5")],
                default=0,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(5),
                ],
            ),
        ),
        migrations.CreateModel(
            name="FarmerReview",
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
                    "rating",
                    models.IntegerField(
                        choices=[
                            (0, "0"),
                            (1, "1"),
                            (2, "2"),
                            (3, "3"),
                            (4, "4"),
                            (5, "5"),
                        ],
                        default=0,
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(5),
                        ],
                    ),
                ),
                ("review", models.TextField()),
                ("date", models.DateTimeField(auto_now_add=True)),
                (
                    "farmer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="farmer_reviews",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
