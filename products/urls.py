from django.contrib import admin
from django.urls import path, include
from .views import ProductList, ProductDetail, CreateProduct, DeleteProduct, UpdateProduct, CreateBox, BoxDetail, PendingBoxList, PendingDecision, AddProductToBox

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
    path("pending/", PendingBoxList.as_view(), name="pending"),
    path("decision/<int:pk>/", PendingDecision.as_view(), name="decision"),
    path("<int:pk>/add_to_box/", AddProductToBox.as_view(), name="add_to_box"),
]