from django.contrib import admin
from django.urls import path, include
from .views import CreateProductReview

app_name = "reviews"

urlpatterns = [
    path("<int:pk>/add_review/", CreateProductReview.as_view(), name="add_review"),
]