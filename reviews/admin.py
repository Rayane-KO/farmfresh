from django.contrib import admin
from .models import ProductReview, FarmerReview

# Register your models here.
admin.site.register(ProductReview)
admin.site.register(FarmerReview)