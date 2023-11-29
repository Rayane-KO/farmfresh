from collections.abc import Mapping
from typing import Any
from django import forms
from django.core.files.base import File
from django.db.models.base import Model
from django.forms.utils import ErrorList
from products.models import Product

class ProductCreationForm(forms.ModelForm):

    class Meta:
        fields = ("name", "category", "description", "unit", "price", "available", "image")
        model = Product

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  
        self.fields["name"].label = "Product Name"
        self.fields["category"].label = "Product Category" 
        self.fields["description"].label = "Description of the product"
        self.fields["price"].label = "Product price"
        self.fields["unit"].label = "Price per piece/kg?"