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

"""
Views for handeling order management:
    OrderList: list of the elements in the users order
    OrderDetail: a detailed view of an order
    PaymentPage: view where cart is turned into an order
"""

class OrderList(LoginRequiredMixin, ListView):
    login_url = "accounts:login"
    model = Order
    template_name = "orders/order_list.html"
    context_object_name = "orders"

    def get_queryset(self):
        # get the orders of the user
        return Order.objects.filter(user=self.request.user)
    
class OrderDetail(DetailView):
    model = Order
    template_name = "orders/order_detail.html"
    context_object_name = "order"
    # Django ensures that the context_object is the correct order (uses the pk given in url)


class PaymentPage(LoginRequiredMixin, TemplateView):
    template_name = "orders/payment_page.html" 

    def post(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        # for development let all payments be successfull
        payment_successful = True
        # if the cart is empty redirect the user to the shop and notify
        if not cart.cartitem_set.exists():
            messages.warning(request, "Your cart is empty. Buy some products to place order!")
            return redirect("products:product_list")
        if payment_successful:
            # create an order when payment successfull
            order = Order.objects.create(user=cart.user, total=cart.total)
            # create an order item for each cart item
            for item in cart.cartitem_set.all():
                OrderItem.objects.create(
                    order=order,
                    item=item.item,
                    quantity=item.quantity,
                    total=item.total
                )
            # delete all the items in the cart
            cart.cartitem_set.all().delete()
            # notify the user for successfull order placement
            messages.success(request, "Order placed successfully!")    
            return redirect("home")
        else:
            messages.error(request, "An error occured. Please try again.")
            return redirect("cart:cart_items")

