from typing import Any
from django import http
from django.shortcuts import render
from products.models import Category, Product, Box
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
from view_breadcrumbs import ListBreadcrumbMixin, DetailBreadcrumbMixin
from fuzzywuzzy import fuzz
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
import logging

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
        if query:
            return self.get_products_by_search(query)
        elif farmer_id:
            return self.get_products_by_farmer(farmer_id)
        else:
            return self.get_all_products()
        
    def get_products_by_farmer(self, farmer_id):
        # return the products of a specific farmer
        farmer = get_object_or_404(User, pk=farmer_id)
        return Product.objects.filter(seller=farmer)
    
    def get_products_by_search(self, search):
        products = Product.objects.all()
        # use token sort because it doesn't care in what order, it accounts for similar for similar strings
        search_result = (
            product for product in products
            if fuzz.token_sort_ratio(search, product.name) >= 70
                or fuzz.token_sort_ratio(search, product.seller) >= 70
                  or fuzz.token_sort_ratio(search, product.description) >= 70
        )
        return search_result
    
    def get_all_products(self):
        return Product.objects.all()
        
    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        boxes = Box.objects.all() 
        context["boxes"] = boxes
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

    def get_product_id(self, name, access_token):
        api_url = f"https://platform.fatsecret.com/rest/server.api?method=foods.search&search_expression={name}&format=json"
        headers = {"Authorization": "Bearer " + access_token}
        response = requests.get(api_url, headers=headers)
        if response.ok:
            data = response.json()
            product_list = data.get("foods", {}).get("food", [])
            product_id = ""
            if product_list:
                product_id = product_list[0].get("food_id")
            else: product_id = None
            return product_id
        else: return None

    def get_nutritional_info(self, product_id, access_token):
        api_url = f"https://platform.fatsecret.com/rest/server.api?method=food.get.v3&food_id={product_id}&format=json"
        headers = {"Authorization": "Bearer " + access_token}
        response = requests.get(api_url, headers=headers)
        if response.ok:
            data = response.json()
            nutritional_info = data.get("food").get("servings", {}).get("serving", [])[0]
            return nutritional_info
        else: {}
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = context["product"]
        context["reviews"] = product.review_set.all()
        access_token = self.get_access_token()
        if access_token:
            product_id = self.get_product_id(product.name, access_token)
            if product_id:
                nutritional_info = self.get_nutritional_info(product_id, access_token)
                context["nutritional_info"] = nutritional_info  
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
        context["products"] = box.products.all()
        return context
    
    
    
    

    