from django.db import models
from accounts.models import User
from products.models import Product

# Create your models here.
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=10, decimal_places=2, default="0.00")

    def __str__(self):
        return f"Cart of {self.user.username}"
    
    def save(self, *args, **kwargs):
        items = self.cartitem_set.all()
        self.total = sum(item.total for item in items)
        return super().save(*args, **kwargs)
    
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default="0.00")

    def  __str__(self):
        return f"{self.quantity} {self.product.name} in cart"
    
    def save(self, *args, **kwargs):
        self.total = self.product.price*self.quantity
        return super().save(*args, **kwargs)