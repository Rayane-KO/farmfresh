from typing import Any
from django.db.models.query import QuerySet
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView
from .models import Order, OrderItem
from accounts.models import User
from cart.models import Cart, CartItem
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

class OrderList(ListView):
    model = Order
    template_name = "orders/order_list.html"
    context_object_name = "orders"

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
    
class OrderDetail(DetailView):
    model = Order
    template_name = "orders/order_detail.html"
    context_object_name = "order"


class PaymentPage(LoginRequiredMixin, TemplateView):
    template_name = "orders/payment_page.html" 

    def post(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        payment_successful = True

        if payment_successful:
            order = Order.objects.create(user=cart.user, total=cart.total)
            for item in cart.cartitem_set.all():
                OrderItem.objects.create(
                    order=order,
                    item=item.item,
                    quantity=item.quantity,
                    total=item.total
                )
            cart.cartitem_set.all().delete()
            messages.success(request, "Order placed successfully!")    
            return redirect("home")
        else:
            messages.error(request, "An error occured. Please try again.")
            return redirect("cart:cart_items")

