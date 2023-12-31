# Generated by Django 4.1 on 2023-12-03 13:05

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("products", "0005_product_avg_rating"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="product",
            name="category",
        ),
        migrations.AddField(
            model_name="product",
            name="categories",
            field=models.ManyToManyField(
                related_name="products", to="products.category"
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="description",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="product",
            name="price",
            field=models.DecimalField(decimal_places=2, default=1.99, max_digits=10),
        ),
        migrations.CreateModel(
            name="Box",
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
                ("name", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True, null=True)),
                (
                    "price",
                    models.DecimalField(decimal_places=2, default=1.99, max_digits=10),
                ),
                ("available", models.BooleanField(default=True)),
                ("date", models.DateTimeField(auto_now_add=True)),
                ("image", models.ImageField(upload_to="images/")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("approved", "Approved"),
                            ("reejected", "Rejected"),
                        ],
                        default="Pending",
                        max_length=20,
                    ),
                ),
                (
                    "asker",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "farmers",
                    models.ManyToManyField(
                        related_name="boxes", to=settings.AUTH_USER_MODEL
                    ),
                ),
                (
                    "products",
                    models.ManyToManyField(related_name="boxes", to="products.product"),
                ),
            ],
        ),
    ]
