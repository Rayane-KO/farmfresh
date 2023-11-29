from typing import Any
from django import http
from django.shortcuts import render
from products.models import Category, Product
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
import base64
import requests

User = get_user_model()

# Create your views here.
class ProductList(SelectRelatedMixin, ListView):
    model = Product
    select_related = ("seller",)
    template_name = "products/product_list.html"
    context_object_name = "products"
    
    def get_queryset(self):
        query = self.request.GET.get("q")
        farmer_id = self.kwargs.get("pk")
        if query:
            return Product.objects.filter(Q(name__icontains=query) | Q(description__icontains=query))
        elif farmer_id:
            farmer = get_object_or_404(User, pk=farmer_id)
            return Product.objects.filter(seller=farmer)
        else:
            return Product.objects.all()
    

class SellerProductList(ListView):
    model = Product
    template_name = "products/farmer_product_list.html"

    def get_queryset(self):
        try:
            self.seller = User.objects.prefetch_related("products").get(username__iexact=self.kwargs.get("username"))

        except User.DoesNotExist:
            raise Http404

        else:
            return self.seller.products.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["seller"] = self.seller
        return context
    
class ProductDetail(SelectRelatedMixin, DetailView):
    model = Product
    select_related = ("seller",)
    template_name = "products/product_detail.html"
    form_class = ProductReviewForm

    def get_queryset(self):
        return super().get_queryset().prefetch_related("review_set")
    
    def get_access_token(self):
        client_id = "212cb9126d1849aaaa9b0564f5eb8308"
        client_secret = "fdef2f80a1264bacaed6244cf0357382"
        token_url = "https://oauth.fatsecret.com/connect/token"
        data = {
            "grant_type": "client_credentials",
            "scope": "basic"
        }
        headers = {
            "Authorization": "Basic " + base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode('utf-8')
        }
        response = requests.post(token_url, data=data, headers=headers)
        if response.ok:
            return response.json().get("access_token")
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
    
    
    
    
    
    
    
    

    