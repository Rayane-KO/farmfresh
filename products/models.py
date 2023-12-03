from collections.abc import Iterable
from django.db import models
from django.db.models import Avg
from accounts.models import User

"""
    Category: represents a product category
    Product: represent a product that has next attributes:
        - name: the name of the product
        - category: a foreign key that is the category
        - description: a description of the product
        - price: price of the product
        - unit: is the unit for the price (piece or kg)
        - available: boolean that tells if a product is available
        - date: date the product was added
        - seller: farmer that sells the product
        - image: image of the product
        - avg_rating: average rating of the product on 5
"""
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
    categories = models.ManyToManyField(Category, related_name="products")
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=1.99)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES)
    available = models.BooleanField(default=True)
    date = models.DateTimeField(auto_now_add=True)
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="images/")
    avg_rating = models.DecimalField(max_digits=2, decimal_places=1, default=0)

    def __str__(self):
        return self.name 
    
class Box(models.Model):
    STATUS = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("reejected", "Rejected"),
    ]

    name = models.CharField(max_length=200)
    products = models.ManyToManyField(Product, related_name="boxes")
    farmers = models.ManyToManyField(User, blank=True, related_name="boxes")
    asker = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=1.99)
    available = available = models.BooleanField(default=True)
    date = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to="images/")
    status = models.CharField(max_length=20, choices=STATUS, default="Pending")
    avg_rating = models.DecimalField(max_digits=2, decimal_places=1, default=0)

    def __str__(self):
        return self.name 