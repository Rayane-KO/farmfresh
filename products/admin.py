from django.contrib import admin
from products.models import Category, Product, Box, Invitation, BoxItem

class ProductAdmin(admin.ModelAdmin):
    list_display = ("pk", "name")

class BoxAdmin(admin.ModelAdmin):
    list_display = ("pk", "name")

# Register your models here.
admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
admin.site.register(Box, BoxAdmin)
admin.site.register(BoxItem)
admin.site.register(Invitation)