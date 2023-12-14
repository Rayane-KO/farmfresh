from typing import Any
from django import http
from django.shortcuts import render, redirect
from products.models import Category, Product, Box, Invitation
from django.views.generic import View, ListView, DetailView, CreateView, DeleteView, UpdateView
from django.contrib.auth import get_user_model
from braces.views import SelectRelatedMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from products import forms
from reviews.forms import ProductReviewForm
from reviews.models import ProductReview
from django.urls import reverse_lazy, reverse
from django.http import Http404, JsonResponse
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.conf import settings
from datetime import datetime, timedelta
from django.core.cache import cache
import base64
import requests
from itertools import chain
from view_breadcrumbs import ListBreadcrumbMixin, DetailBreadcrumbMixin
from fuzzywuzzy import fuzz
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
import logging
import json


User = get_user_model()

# Sources:
# Fuzzy search: https://www.datacamp.com/tutorial/fuzzy-string-python

"""
    PRODUCT
"""

class ProductList(ListBreadcrumbMixin, ListView):
    model = Product
    template_name = "products/product_list.html"
    context_object_name = "products"
    
    def get_queryset(self):
        query = self.request.GET.get("q")
        farmer_id = self.kwargs.get("pk")
        category = self.request.GET.get("category")
        sort_by = self.request.GET.get("sort_by")
        if query:
            return self.get_products_by_search(query)
        elif category:
            queryset = self.get_products_by_category(category)
        elif farmer_id:
            return self.get_products_by_farmer(farmer_id)
        else:
            queryset = self.get_all_products()

        products = queryset.get("products")
        boxes = queryset.get("boxes")
        if sort_by == "ascending":
            products = products.order_by("price")
            boxes = boxes.order_by("price")
        elif sort_by == "descending":
            products = products.order_by("-price")
            boxes = boxes.order_by("-price")
        elif sort_by == "best_rated":
            products = products.order_by("-avg_rating")
            boxes = boxes.order_by("-avg_rating")
        sorted_products = {"products": products, "boxes": boxes}
        return sorted_products

        
    def get_products_by_farmer(self, farmer_id):
        # return the products of a specific farmer
        farmer = get_object_or_404(User, pk=farmer_id)
        products = Product.objects.filter(seller=farmer)
        boxes = Box.objects.filter(Q(asker=farmer) | Q(farmers=farmer))
        return {"products": products, "boxes": boxes}
    
    def get_products_by_category(self, category):
        products = Product.objects.filter(categories__name__iexact=category)
        boxes = Box.objects.all()
        if category.lower() != "box":
            return {"products": products}
        else: 
            return {"products": products, "boxes": Box.objects.all()}
    
    def get_products_by_search(self, search):
        products = Product.objects.all()
        boxes = Box.objects.all()
        # use token sort because it doesn't care in what order, it accounts for similar for similar strings
        product_search_result = (
            product for product in products
            if fuzz.token_sort_ratio(search, product.name) >= 70
                or fuzz.token_sort_ratio(search, product.seller) >= 70
                  or fuzz.token_sort_ratio(search, product.description) >= 70
        )
        box_search_result = (
            box for box in boxes
            if fuzz.token_sort_ratio(search, box.name) >= 70
                or fuzz.token_sort_ratio(search, box.asker) >= 70
                  or fuzz.token_sort_ratio(search, box.description) >= 70
        )
        return {"products": product_search_result, "boxes": box_search_result}
    
    def get_all_products(self):
        products = Product.objects.all()
        boxes = Box.objects.all()
        """
        user_id = self.request.user.pk
        favorites_id = "favorites_" + str(user_id)
        fav = self.request.session.get(favorites_id)
        if fav:
            try:
                favorites = [int(pk) for pk in json.loads(fav)]
            except (json.JSONDecodeError, ValueError):
                favorites = []
        else:
            favorites = []
        print(fav)    
        fav_products = [product for product in products if product.seller.pk in favorites]
        other_products = [product for product in products if product.seller.pk not in favorites]
        products = fav_products + other_products
        """
        return {"products": products, "boxes": boxes}
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        return context
    
    
    
class ProductDetail(DetailBreadcrumbMixin, SelectRelatedMixin, DetailView):
    model = Product
    select_related = ("seller",)
    template_name = "products/product_detail.html"
    form_class = ProductReviewForm

    def get_queryset(self):
        return super().get_queryset().prefetch_related("review_set")
    
    def get_access_token(self):
        client_id = settings.FATSECRET_CLIENT_ID
        client_secret = settings.FATSECRET_CLIENT_SECRET
        token_url = "https://oauth.fatsecret.com/connect/token"
        data = {
            "grant_type": "client_credentials",
            "scope": "basic"
        }
        headers = {
            "Authorization": "Basic " + base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode('utf-8')
        }
        # check if the access token is available in the cache
        cached_token = cache.get("access_token")
        if cached_token:
            return cached_token
        response = requests.post(token_url, data=data, headers=headers)
        if response.ok:
            access_data = response.json()
            access_token = access_data.get("access_token")
            expires_in = access_data.get("expires_in")
            # each access token has an expires_in field so cache the token
            # with a timeout equal to this field
            if access_token and expires_in:
                cache.set("access_token", access_token, timeout=expires_in)
                return access_token
        else: None

    def get_product_id(self, pk, access_token):
        product = Product.objects.get(pk=pk)
        if product.fatsecret_id:
            return product.fatsecret_id
        else:
            api_url = f"https://platform.fatsecret.com/rest/server.api?method=foods.search&search_expression={product.name}&format=json"
            headers = {"Authorization": "Bearer " + access_token}
            response = requests.get(api_url, headers=headers)
            if response.ok:
                data = response.json()
                product_list = data.get("foods", {}).get("food", [])
                if product_list:
                    product.fatsecret_id = product_list[0].get("food_id")
                    product.save()
                    return product.fatsecret_id
                else: return None
            else: return None

    def process_nutritional_info(self, info):
        processed_info = {}
        items = info.items()
        serving = ""
        for key, value in items:
            if key in ["is_default", "serving_url", "measurement_description", "metric_serving_amount", "metric_serving_unit", "serving_id"]:
                continue
            elif key == "serving_description":
                serving = value
                continue
            label = key.replace("_", " ").capitalize()
            processed_info[label] = value
        return (serving, processed_info)

    def get_nutritional_info(self, product_id, access_token):
        api_url = f"https://platform.fatsecret.com/rest/server.api?method=food.get.v3&food_id={product_id}&format=json"
        headers = {"Authorization": "Bearer " + access_token}
        response = requests.get(api_url, headers=headers)
        if response.ok:
            data = response.json()
            nutritional_info = data.get("food").get("servings", {}).get("serving", [])[0]
            return self.process_nutritional_info(nutritional_info)
        else: ()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = context["product"]
        context["review_type"] = "product"
        context["reviews"] = product.review_set.all()
        access_token = self.get_access_token()
        if access_token:
            product_id = self.get_product_id(product.pk, access_token)
            if product_id:
                nutritional_info = self.get_nutritional_info(product_id, access_token)
                context["serving"] = nutritional_info[0]
                context["nutritional_info"] = nutritional_info[1]
        return context          
    
class CreateProduct(SelectRelatedMixin, LoginRequiredMixin, CreateView):
    form_class = forms.ProductCreationForm
    model = Product
    template_name = "products/product_form.html"

    def form_valid(self, form):
        self.object = form.save(commit=False)
        user_instance = User.objects.get(pk=self.request.user.pk)
        self.object.seller = user_instance
        self.object.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("products:product_detail", kwargs={"pk": self.object.pk})
    

class DeleteProduct(LoginRequiredMixin, DeleteView):
    model = Product
    success_url = reverse_lazy("products:all")
    template_name = "products/confirm_delete.html"

    def get_queryset(self):
        return super().get_queryset().filter(pk=self.kwargs.get("pk"))

    def delete(self, *args, **kwargs):
        product = self.get_object()
        if self.request.user != product.seller:
            raise Http404("You don't Have the permissions")
        return super().delete(*args, **kwargs)
    
class UpdateProduct(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = forms.ProductCreationForm
    template_name = "products/product_form.html"

    def get_queryset(self):
        return super().get_queryset().filter(pk=self.kwargs.get("pk"))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_update"] = True
        return context
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse("products:product_detail", kwargs={"pk": self.object.pk})
    
    def dispatch(self, request, *args, **kwargs):
        product = self.get_object()
        if request.user != product.seller:
            raise Http404("You do not have the permission for this action!")
        return super().dispatch(request, *args, **kwargs)
    
"""
    BOX
"""

class CreateBox(CreateView):
    form_class = forms.BoxCreationForm
    model = Box
    template_name = "products/box_form.html"
    
    def get_success_url(self):
        return reverse("products:product_list")
    
    def form_valid(self, form):
        products = form.cleaned_data["products"]
        invited_farmers_pk = form.cleaned_data["farmers"]
        invited_farmers = User.objects.filter(pk__in=invited_farmers_pk)
        price = sum(product.price for product in products)
        form.instance.price = price
        form.instance.asker = self.request.user
        form.instance.save()
        for farmer in invited_farmers:
            Invitation.objects.create(
                inviting_farmer = self.request.user,
                invited_farmer = farmer,
                box = form.instance
            )
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class BoxDetail(DetailView):
    model = Box
    template_name = "products/box_detail.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        box = self.object
        box_products = box.products.all()
        farmers_product = Product.objects.filter(seller=self.request.user)
        farmers_product = farmers_product.exclude(pk__in=box_products.values_list("pk", flat=True))
        invitations = Invitation.objects.filter(box=box)
        context["products"] = box_products
        context["farmers_products"] = farmers_product
        context["pending"] = invitations
        return context

class PendingBoxList(ListView):
    model = Box
    template_name = "products/pending_list.html"
    context_object_name = "pending_boxes"

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            pending_boxes = Box.objects.filter(status="pending")
            confirmed_boxes = [box for box in pending_boxes if box.is_confirmed()]
            return confirmed_boxes
        elif user.is_farmer:
            return Box.objects.filter(Q(asker=user) | Q(farmers__in=[user]))  
        else: return None #later Error    

class PendingDecision(View):
    def post(self, request, *args, **kwargs):
        box_id = self.kwargs.get("pk")
        action = request.POST.get("action")
        user = request.user

        if user.is_staff:
            try:
                box = Box.objects.get(pk=box_id)
                if action == "approve":
                    box.status = "approved"
                    box.save()
                elif action == "reject":
                    box.status = "rejected"
                    box.save()
            except Box.DoesNotExist:
                pass
        if user.is_farmer:
            try: 
                box = Box.objects.get(pk=box_id)
                invitation = Invitation.objects.get(invited_farmer=user, box=box)
                if action == "accept":
                    invitation.status = "accepted"
                    invitation.save()
                elif action == "reject":
                    invitation.status = "rejected"
                    box.farmers.remove(user)
                    box.save()
                    invitation.save() 
                elif action == "confirm":
                    box.confirmed.add(user)
                    box.save()
            except Box.DoesNotExist:
                pass

        return redirect("products:pending")
    
class AddProductToBox(UpdateView):
    model = Box
    template_name = "products/box_detail.html"
    fields = []

    def get_success_url(self):
        return reverse_lazy("products:box_detail", kwargs={"pk": self.kwargs.get("pk")})
    
    def post(self, request, *args, **kwargs):
        selected_products_pk = json.loads(request.body).get("products")
        selected_products = Product.objects.filter(pk__in=selected_products_pk)
        box = self.get_object()
        box.products.add(*selected_products)
        box.save()
        return JsonResponse({"status": "success"})
    
    
    
    
    
    

    