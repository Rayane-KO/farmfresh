from django.contrib import admin
from .models import ProductReview, FarmerReview, FarmerReply

# Register your models here.

admin.site.register(ProductReview)
admin.site.register(FarmerReview)
admin.site.register(FarmerReply)