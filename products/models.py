from collections.abc import Iterable
from django.db import models
from django.db.models import Avg
from accounts.models import User

# Create your models here.
class Category(models.Model):

    name = models.CharField(max_length=200, db_index=True)

    def __str__(self):
        return self.name

class Product(models.Model):

    UNIT_CHOICES = [
        ("kg", "Kilogram"),
        ("piece", "Piece"),
    ]

    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, related_name="product", on_delete=models.CASCADE)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default="1.99")
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES)
    available = models.BooleanField(default=True)
    date = models.DateTimeField(auto_now_add=True)
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="images/")
    avg_rating = models.DecimalField(max_digits=2, decimal_places=1, default=0)

    def __str__(self):
        return self.name 