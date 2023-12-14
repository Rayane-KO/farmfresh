from typing import Any
from django import http
from django.shortcuts import render, redirect
from products.models import Category, Product
from cart.models import CartItem, Cart
from django.views.generic import View, ListView, DetailView, CreateView, DeleteView, UpdateView
from django.contrib.auth import get_user_model
from braces.views import SelectRelatedMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from products import forms
from django.urls import reverse_lazy, reverse
from django.http import Http404, JsonResponse

# Create your views here.
class CartItemList(SelectRelatedMixin, LoginRequiredMixin, ListView):
    model = CartItem
    select_related = ("user",)
    template_name = "cart/cart_list.html"
    context_object_name = "cart_items"

    def get_queryset(self):
        user_cart, created = Cart.objects.get_or_create(user=self.request.user)
        return CartItem.objects.filter(cart=user_cart)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_cart = Cart.objects.get(user=self.request.user)
        context["cart"] = user_cart
        return context
    
    
class CartAddItem(LoginRequiredMixin, View):
    login_url = "accounts:login"

    def post(self, request, *args, **kwargs):
        user_cart, created = Cart.objects.get_or_create(user=request.user)
        cart_product = Product.objects.get(pk=kwargs.get("pk"))
        cart_item, created = CartItem.objects.get_or_create(cart=user_cart, product=cart_product)

        if not created:
            cart_item.quantity += 1
            cart_item.save()
            user_cart.save()

        return JsonResponse({"status": "success"})
    
    def get(self, request, *args, **kwargs):
        cart_product = Product.objects.get(pk=kwargs.get("pk"))
        return render(request, "index.html")
    
class CartRemoveItem(LoginRequiredMixin, DeleteView):
    def post(self, request, *args, **kwargs):
        user_cart, created = Cart.objects.get_or_create(user=request.user)
        cart_product = Product.objects.get(pk=kwargs.get("pk"))

        if not request.user.is_authenticated:
            return JsonResponse({"status": "not logged in"})

        try:
            cart_item = CartItem.objects.get(cart=user_cart, product=cart_product)
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
                user_cart.save()
            else: 
                cart_item.delete()
                user_cart.save()    

            return JsonResponse({"status": "success"})
        
        except CartItem.DoesNotExist:
            return JsonResponse({"status": "does not exist"})