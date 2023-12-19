from collections.abc import Mapping
from typing import Any
from django import forms
from django.core.files.base import File
from django.db.models.base import Model
from django.forms.utils import ErrorList
from products.models import Product, Box, BoxItem, Category
from accounts.models import User
from django.forms import inlineformset_factory

class ProductCreationForm(forms.ModelForm):
    categories = forms.MultipleChoiceField(
        choices=[],
        widget=forms.CheckboxSelectMultiple
    )

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
        self.fields["categories"].choices = [
            (category.pk, category.name) for category in Category.objects.all()
        ]

class BoxCreationForm(forms.ModelForm):
    farmers = forms.MultipleChoiceField(
        choices=[],
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        fields = ("name", "description", "farmers", "image")
        model = Box

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["farmers"].choices = [
            (farmer.pk, farmer.username) for farmer in User.objects.filter(is_farmer = True).exclude(pk=user.pk)
        ]

class BoxItemForm(forms.ModelForm):
    class Meta:
        fields = ("product", "quantity",)
        model = BoxItem

BoxItemFormSet = inlineformset_factory(Box, BoxItem, form=BoxItemForm, extra=1, can_delete=False)