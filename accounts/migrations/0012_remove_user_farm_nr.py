# Generated by Django 4.1 on 2023-12-03 16:10

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0011_alter_user_farm_nr"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="farm_nr",
        ),
    ]
