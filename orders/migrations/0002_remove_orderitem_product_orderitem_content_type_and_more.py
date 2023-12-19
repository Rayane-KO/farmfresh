# Generated by Django 4.1 on 2023-12-18 17:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="orderitem",
            name="product",
        ),
        migrations.AddField(
            model_name="orderitem",
            name="content_type",
            field=models.ForeignKey(
                default=0,
                limit_choices_to={"model__in": ["product", "box"]},
                on_delete=django.db.models.deletion.CASCADE,
                to="contenttypes.contenttype",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="orderitem",
            name="object_id",
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
    ]