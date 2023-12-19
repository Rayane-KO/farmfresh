from django.contrib import admin
from django.urls import path, include
from .views import PaymentPage, OrderList, OrderDetail

app_name = "orders"

urlpatterns = [
    path("orders/", OrderList.as_view(), name="orders"),
    path("order-detail/<int:pk>", OrderDetail.as_view(), name="order_detail"),
    path("payment/", PaymentPage.as_view(), name="payment"),
]