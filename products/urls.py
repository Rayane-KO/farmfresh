from django.contrib import admin
from django.urls import path, include
from .views import ProductList, ProductDetail, CreateProduct, DeleteProduct, UpdateProduct, CreateBox, BoxDetail

app_name = "products"

urlpatterns = [
    path("", ProductList.as_view(), name="product_list"),
    path("farmer/<int:pk>/", ProductList.as_view(), name="farmer_products"),
    path("product/<int:pk>/", ProductDetail.as_view(), name="product_detail"),
    path("create/", CreateProduct.as_view(), name="create_product"),
    path("<int:pk>/delete/", DeleteProduct.as_view(), name="delete_product"),
    path("<int:pk>/update/", UpdateProduct.as_view(), name="update_product"),
    path("createbox/", CreateBox.as_view(), name="create_box"),
    path("box/<int:pk>/", BoxDetail.as_view(), name="box_detail"),
]