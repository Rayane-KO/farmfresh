from django.contrib import admin
from django.urls import path, include
from .views import CartItemList, CartAddItem, CartRemoveItem

app_name = "cart"

urlpatterns = [
    path("cart-items", CartItemList.as_view(), name="cart_items"),
    path("<int:pk>/add-to-cart/", CartAddItem.as_view(), name="add_to_cart"),
    path("<int:pk>/remove-from-cart/", CartRemoveItem.as_view(), name="remove_from_cart"),
]