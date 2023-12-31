# Generated by Django 4.1 on 2023-12-14 12:31

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0013_invitation"),
    ]

    operations = [
        migrations.AddField(
            model_name="invitation",
            name="invite_date",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
    ]
