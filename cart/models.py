from django.db import models
from accounts.models import User
from products.models import Product
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

# Create your models here.
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=10, decimal_places=2, default="0.00")

    def __str__(self):
        return f"Cart of {self.user.username}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        items = self.cartitem_set.all()
        self.total = sum(item.total for item in items)
        return super().save(*args, **kwargs)
    
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, limit_choices_to={'model__in': ['product', 'box']})
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey("content_type", "object_id")
    quantity = models.PositiveIntegerField(default=1, blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default="0.00")

    def __str__(self):
        return f"{self.quantity} {self.item.name} in cart"

    def save(self, *args, **kwargs):
        model_class = self.content_type.model_class()
        item = model_class.objects.get(pk=self.item.pk)
        self.total = item.price*self.quantity
        return super().save(*args, **kwargs)