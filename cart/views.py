from typing import Any
from django import http
from django.shortcuts import render, redirect, get_object_or_404
from products.models import Category, Product, Box
from cart.models import CartItem, Cart
from view_breadcrumbs import ListBreadcrumbMixin, DetailBreadcrumbMixin
from django.views.generic import View, ListView, DetailView, CreateView, DeleteView, UpdateView
from django.contrib.auth import get_user_model
from braces.views import SelectRelatedMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from products import forms
from django.urls import reverse_lazy, reverse
from django.http import Http404, JsonResponse
from django.contrib.contenttypes.models import ContentType

"""
Views for handeling cart management:
    CartItemList: list of the elements in the users cart
    CartAddItem: allows to add new items in the users cart
    CartRemoveItem: allows to remove items in the users cart
    CartCount: used to get the number of elements in the cart (per type, not quantity)
"""

class CartItemList(LoginRequiredMixin, ListView):
    model = CartItem
    template_name = "cart/cart_list.html"
    context_object_name = "cart_items"

    # this functions specifies what should the context_object should contain
    def get_queryset(self):
        # get or create the cart of the user
        user_cart, created = Cart.objects.get_or_create(user=self.request.user)
        # if cart was created save in database
        if created:
            user_cart.save()
        # get only the items in the cart of the user
        return CartItem.objects.filter(cart=user_cart)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_cart = Cart.objects.get(user=self.request.user)
        # add also the users cart to be able to render information about the cart (total price)
        context["cart"] = user_cart
        return context
       
class CartAddItem(LoginRequiredMixin, CreateView):
    login_url = "accounts:login"

    # handle post to add the product to the cart
    def post(self, request, *args, **kwargs):
        # first get the cart of the user or create it if it doesn't exist
        user_cart, created = Cart.objects.get_or_create(user=request.user)
        # get the type of the product you want to add (Product or Box)
        product_type = kwargs.get("type")
        # get the correct item depending on the type
        if product_type == "product":
            product = get_object_or_404(Product, pk=kwargs.get("pk"))
        elif product_type == "box":
            product = get_object_or_404(Box, pk=kwargs.get("pk"))
        # get the model of the item you want to add to be able to get the cart item
        content_type = ContentType.objects.get_for_model(product)
        object_id = product.pk
        cart_item, created = CartItem.objects.get_or_create(cart=user_cart, content_type=content_type, object_id=object_id)
        # if the cart item exists just update the quantity (when you create an item quantity is automatically on 1)
        if not created:
            cart_item.quantity += 1
            cart_item.save()
            user_cart.save()   
        # count the number of different items in cart
        cart_count = CartItem.objects.filter(cart=user_cart).count()
        # return the json response with the information to update frontend
        return JsonResponse({
            "cart_count": cart_count, 
            "quantity": cart_item.quantity,
            "subtotal": cart_item.total,
            "total": user_cart.total
        })
    
class CartRemoveItem(LoginRequiredMixin, DeleteView):
    login_url = "accounts:login"

    def post(self, request, *args, **kwargs):
        # same logic as add item
        user_cart = Cart.objects.get(user=request.user)
        product_type = kwargs.get("type")
        if product_type == "product":
            product = get_object_or_404(Product, pk=kwargs.get("pk"))
        elif product_type == "box":
            product = get_object_or_404(Box, pk=kwargs.get("pk"))
        # check if you can delete an item from a cart
        try:
            content_type = ContentType.objects.get_for_model(product)
            object_id = product.pk
            cart_item = CartItem.objects.get(cart=user_cart, content_type=content_type, object_id=object_id)
            # if the item is already in cart with quantity more than 1 then just decrement the quantity
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                # otherwise quantity is 1 and you remove so delete item from cart
                cart_item.delete()
            # save the cart to database
            user_cart.save()    
            cart_count = CartItem.objects.filter(cart=user_cart).count()
            return JsonResponse({
                "cart_count": cart_count, 
                "quantity": cart_item.quantity,
                "subtotal": cart_item.total,
                "total": user_cart.total
            })
        except CartItem.DoesNotExist:
            # if cart does not exists return an error status
            return JsonResponse({"status": "Does not exist"})
    
class CartCount(View):
    # handle the request and return the count of cart
    def get(self, request, *args, **kwargs):
        cart, created = Cart.objects.get_or_create(user=request.user)
        if created:
            cart.save()
        cart_count = CartItem.objects.filter(cart=cart).count()
        return JsonResponse({"cart_count": cart_count})
