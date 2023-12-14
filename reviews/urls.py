from django.contrib import admin
from django.urls import path, include
from .views import CreateProductReview, CreateFarmerReview, CreateFarmerReply

app_name = "reviews"

urlpatterns = [
    path("<int:pk>/add_product_review/", CreateProductReview.as_view(), name="add_product_review"),
    path("<int:pk>/add_farmer_review/", CreateFarmerReview.as_view(), name="add_farmer_review"),
    path("<str:type>/<int:pk>/review_reply/", CreateFarmerReply.as_view(), name="review_reply")
]