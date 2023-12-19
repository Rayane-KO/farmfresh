from typing import Any
from django import http
from django.shortcuts import render, redirect, get_object_or_404
from products.models import Category, Product, Box
from cart.models import CartItem, Cart
from django.views.generic import View, ListView, DetailView, CreateView, DeleteView, UpdateView
from django.contrib.auth import get_user_model
from braces.views import SelectRelatedMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from products import forms
from django.urls import reverse_lazy, reverse
from django.http import Http404, JsonResponse
from django.contrib.contenttypes.models import ContentType

# Create your views here.
class CartItemList(SelectRelatedMixin, LoginRequiredMixin, ListView):
    model = CartItem
    select_related = ("user",)
    template_name = "cart/cart_list.html"
    context_object_name = "cart_items"

    def get_queryset(self):
        user_cart, created = Cart.objects.get_or_create(user=self.request.user)
        user_cart.save()
        return CartItem.objects.filter(cart=user_cart)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_cart = Cart.objects.get(user=self.request.user)
        context["cart"] = user_cart
        return context
    
    
class CartAddItem(View):
    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            user_cart, created = Cart.objects.get_or_create(user=request.user)
            product_type = kwargs.get("type")
            if product_type == "product":
                product = get_object_or_404(Product, pk=kwargs.get("pk"))
            elif product_type == "box":
                product = get_object_or_404(Box, pk=kwargs.get("pk"))

            content_type = ContentType.objects.get_for_model(product)
            object_id = product.pk
            cart_item, created = CartItem.objects.get_or_create(cart=user_cart, content_type=content_type, object_id=object_id)

            if not created:
                cart_item.quantity += 1
                cart_item.save()
                user_cart.save()   
            cart_count = CartItem.objects.filter(cart=user_cart).count()
            return JsonResponse({"cart_count": cart_count, 
                                "quantity": cart_item.quantity,
                                "subtotal": cart_item.total,
                                "total": user_cart.total
                                })
        else:
            return JsonResponse({"redirect": reverse("accounts:login")})
    
class CartRemoveItem(DeleteView):
    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            user_cart = Cart.objects.get(user=request.user)
            product_type = kwargs.get("type")
            if product_type == "product":
                product = get_object_or_404(Product, pk=kwargs.get("pk"))
            elif product_type == "box":
                product = get_object_or_404(Box, pk=kwargs.get("pk"))

            try:
                content_type = ContentType.objects.get_for_model(product)
                object_id = product.pk
                cart_item = CartItem.objects.get(cart=user_cart, content_type=content_type, object_id=object_id)

                if cart_item.quantity > 1:
                    cart_item.quantity -= 1
                    cart_item.save()
                else:
                    cart_item.delete()
                user_cart.save()    
                cart_count = CartItem.objects.filter(cart=user_cart).count()
                return JsonResponse({"cart_count": cart_count, 
                                "quantity": cart_item.quantity,
                                "subtotal": cart_item.total,
                                "total": user_cart.total
                             })
            except CartItem.DoesNotExist:
                return JsonResponse({"status": "Does not exist"})
        else:
            return JsonResponse({"redirect": reverse("accounts:login")})
    
class CartCount(View):
    def get(self, request, *args, **kwargs):
        # Attempt to retrieve the existing Cart instance
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            # If the Cart does not exist, create a new one
            cart = Cart(user=request.user)
            cart.save()

        # Now that the Cart instance is guaranteed to exist, you can proceed
        cart_count = CartItem.objects.filter(cart=cart).count()
        return JsonResponse({"cart_count": cart_count})
