from django.contrib import admin
from django.urls import path, include
from .views import ProductList, SellerProductList, ProductDetail, CreateProduct, DeleteProduct, UpdateProduct

app_name = "products"

urlpatterns = [
    path("all/", ProductList.as_view(), name="all"),
    path("farmer/<int:pk>/", ProductList.as_view(), name="farmer_products"),
    path("<int:pk>/", ProductDetail.as_view(), name="product_detail"),
    path("create/", CreateProduct.as_view(), name="create_product"),
    path("<int:pk>/delete/", DeleteProduct.as_view(), name="delete_product"),
    path("<int:pk>/update/", UpdateProduct.as_view(), name="update_product"),
]