# Generated by Django 4.1 on 2023-11-22 21:56

from django.db import migrations, models
import django_countries.fields
import phonenumber_field.modelfields


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_user_farm_nr_user_is_farmer"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="address",
            field=models.CharField(max_length=300, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="city",
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="country",
            field=django_countries.fields.CountryField(max_length=2, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="latitude",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="longitude",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="phone_number",
            field=phonenumber_field.modelfields.PhoneNumberField(
                blank=True, max_length=128, null=True, region=None
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="state",
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="zip_code",
            field=models.CharField(max_length=20, null=True),
        ),
    ]
