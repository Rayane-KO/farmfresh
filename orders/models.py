from django.db import models
from accounts.models import User
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

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
    order_items = GenericRelation('orders.OrderItem')

    def  __str__(self):
        return f"{self.quantity} {self.item.name} in order"