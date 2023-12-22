from django.db import models
from accounts.models import User
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

"""
Order: represents the order of a user with attributes:
    - user: is the user associated with the order
    - order_date: is the date the order was placed
    - status: is the status of order (examples: pending, shipped...)
    - total: is the total price of the order
CartItem: represents an item of an order with attributes:
    - order: is the order associated with the item
    - content_type: is the relationship with Product or Box
    - object_id: is the id of the item
    - item: is a GenericForeignKey to be able to store a Product or Box in item
    - quantity: is the quantity of an item in the order
    - total: is the subtotal price of the order (quantity * item-price)
"""

class Order(models.Model):
    STATUS = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="Pending", choices=STATUS)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Order of {self.user.username}"
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, limit_choices_to={'model__in': ['product', 'box']})
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey("content_type", "object_id")
    quantity = models.PositiveIntegerField(default=1, blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default="0.00")

    def  __str__(self):
        return f"{self.quantity} {self.item.name} in order"