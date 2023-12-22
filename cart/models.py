from django.db import models
from accounts.models import User
from products.models import Product
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

# Sources:
# - Contenttypes: https://docs.djangoproject.com/en/5.0/ref/contrib/contenttypes/
#                 https://dipbazz.medium.com/how-and-when-to-use-genericforeignkey-in-django-ad88202be0f

"""
Cart: represents the cart of a user with attributes:
    - user: is the user associated with the cart
    - total: is the total price of the cart
CartItem: represents an item of a cart with attributes:
    - cart: is the cart associated with the item
    - content_type: is the relationship with Product or Box
    - object_id: is the id of the item
    - item: is a GenericForeignKey to be able to store a Product or Box in item
    - quantity: is the quantity of an item in the cart
    - total: is the subtotal price of the cart (quantity * item-price)
"""

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=10, decimal_places=2, default="0.00")

    def __str__(self):
        return f"Cart of {self.user.username}"
    
    # when saving the cart of the total price
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

    # when saving a cart item update the subtotal price
    def save(self, *args, **kwargs):
        # get the class of the item
        model_class = self.content_type.model_class()
        item = model_class.objects.get(pk=self.item.pk)
        self.total = item.price*self.quantity
        return super().save(*args, **kwargs)