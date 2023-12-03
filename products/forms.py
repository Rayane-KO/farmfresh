from collections.abc import Mapping
from typing import Any
from django import forms
from django.core.files.base import File
from django.db.models.base import Model
from django.forms.utils import ErrorList
from products.models import Product, Box
from accounts.models import User

class ProductCreationForm(forms.ModelForm):

    class Meta:
        fields = ("name", "categories", "description", "unit", "price", "available", "image")
        model = Product

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  
        self.fields["name"].label = "Product Name"
        self.fields["categories"].label = "Product Categories" 
        self.fields["description"].label = "Description of the product"
        self.fields["price"].label = "Product price"
        self.fields["unit"].label = "Price per piece/kg?"

class BoxCreationForm(forms.ModelForm):
    farmers = forms.MultipleChoiceField(
        choices=[],
        widget=forms.CheckboxSelectMultiple
    )
    products = forms.MultipleChoiceField(
        choices=[],
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        fields = ("name", "products", "description", "farmers", "price", "image")
        model = Box

    def clean_products(self):
        products = self.cleaned_data.get("products")
        return Product.objects.filter(pk__in=products)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["products"].choices = [
            (product.pk, product.name) for product in Product.objects.filter(seller=user)
        ]
        self.fields["farmers"].choices = [
            (farmer.pk, farmer.username) for farmer in User.objects.filter(is_farmer = True).exclude(pk=user.pk)
        ]