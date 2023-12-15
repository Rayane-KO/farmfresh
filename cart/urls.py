from django.contrib import admin
from django.urls import path, include
from .views import CartItemList, CartAddItem, CartRemoveItem, CartCount

app_name = "cart"

urlpatterns = [
    path("cart-items", CartItemList.as_view(), name="cart_items"),
    path("<int:pk>/<str:type>/add-to-cart/", CartAddItem.as_view(), name="add_to_cart"),
    path("<int:pk>/<str:type>/remove-from-cart/", CartRemoveItem.as_view(), name="remove_from_cart"),
    path("cart-count/", CartCount.as_view(), name="count"),
]