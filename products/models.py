from collections.abc import Iterable
from django.db import models
from django.db.models import Avg
from accounts.models import User
from orders.models import OrderItem
from django.contrib.contenttypes.fields import GenericRelation

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
    - fatsecret_id: save the id of the fatsecret api to avoid unnecessary requests
Box: represents a box with next attributes:
    - name: name of the box
    - farmers: farmers invited to the box
    - confirmed: farmers that confirmed the box
    - asker: farmer who created the box
    - description: a description of the box
    - price: is the price of the box
    - available: if the box is available or not
    - date: is the date the box was created
    - image: is an image for the box
    - status: is the current status of the box (example: pending)
    - avg_rating: is the average rating of the box
BoxItem: represents an item in a box with next attributes:
    - box: the box associated with the box item
    - product = is the product associated with the item
    - quantity = the quantity of product in the box
    - price = the subtotal price of the box item
Invitation: represents an invitation sent to other farmers:
    - inviting_farmer: is the farmer who sent the invitation
    - invited_farmer: is the farmer who got the invitation
    - box: is the box associated with the invitation
    - status: status of the invitation (example: accepted)
    - invite_date: is the date the invitation was sent
    - decision_date: is the date the user accepted or rejected the invitation
"""
class Category(models.Model):
    name = models.CharField(max_length=200, db_index=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    UNIT_CHOICES = [
        ("kg", "Kilogram"),
        ("piece", "Piece"),
        ("liter", "Liter"),
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
    order_items = GenericRelation(OrderItem) # to be able to retrieve the orderitems that uses the product

    def __str__(self):
        return self.name 
    
class Box(models.Model):
    STATUS = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    name = models.CharField(max_length=200)
    farmers = models.ManyToManyField(User, blank=True, related_name="boxes")
    confirmed = models.ManyToManyField(User, blank=True, related_name="confirmed")
    asker = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=1.99)
    available = models.BooleanField(default=True)
    date = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to="images/")
    status = models.CharField(max_length=20, choices=STATUS, default="Pending")
    avg_rating = models.DecimalField(max_digits=2, decimal_places=1, default=0)
    order_items = GenericRelation(OrderItem) # to be able to retrieve the orderitems that uses the box
    

    def is_confirmed(self):
        return self.farmers.count() == self.confirmed.count()

    def __str__(self):
        return self.name 
    
class BoxItem(models.Model):
    box = models.ForeignKey(Box, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=1.99)

    def __str__(self):
        return f"{self.quantity} {self.product.name} in {self.box.name}"

    
class Invitation(models.Model):
    STATUS = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    ]

    inviting_farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent")
    invited_farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received")
    box = models.ForeignKey(Box, on_delete=models.CASCADE, related_name="invite")
    status = models.CharField(max_length=20, choices=STATUS, default="Pending")
    invite_date = models.DateTimeField(auto_now_add=True)
    decision_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.inviting_farmer.username} invited {self.invited_farmer.username} for {self.box.name}"