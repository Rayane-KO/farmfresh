# Generated by Django 4.1 on 2023-11-23 14:26

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0003_alter_cartitem_quantity_productreview"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="cartitem",
            name="cart",
        ),
        migrations.RemoveField(
            model_name="cartitem",
            name="product",
        ),
        migrations.RemoveField(
            model_name="productreview",
            name="product",
        ),
        migrations.RemoveField(
            model_name="productreview",
            name="user",
        ),
        migrations.DeleteModel(
            name="Cart",
        ),
        migrations.DeleteModel(
            name="CartItem",
        ),
        migrations.DeleteModel(
            name="ProductReview",
        ),
    ]
