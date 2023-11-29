from typing import Any
from django import http
from django.db import models
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from accounts.forms import UserSignUpForm
from braces.views import SelectRelatedMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import Http404, JsonResponse
from .models import User

from . import forms

# Create your views here.
class SignUp(CreateView):
    form_class = forms.UserSignUpForm
    success_url = reverse_lazy("login")
    template_name = "accounts/signup.html"

class UserDetail(DetailView):
    model = User
    template_name = "accounts/user_detail.html"
    context_object_name = "user_detail"

    def get_object(self, queryset=None):
        if self.kwargs.get("pk"):
            return get_object_or_404(User, pk=self.kwargs.get("pk"))
        elif self.request.user.is_authenticated:
            return self.request.user
        else: None

    def get_queryset(self):
        return super().get_queryset().prefetch_related("farmer_reviews")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        farmer = context["user_detail"]
        context["reviews"] = farmer.farmer_reviews.all()
        return context

class FarmerList(ListView):
    model = User
    template_name = "accounts/farmers_list.html"
    context_object_name = "farmers"

    def get_queryset(self):
        return User.objects.filter(is_farmer=True)
    
    def post(self, request, *args, **kwargs):
        farmers = list(User.objects.filter(is_farmer=True).values("username", "pk", "latitude", "longitude"))
        my_location = (self.request.user.longitude, self.request.user.latitude)
        return JsonResponse({"farmers": farmers, "location": my_location}, safe=False)

    
class UpdateUser(LoginRequiredMixin, UpdateView):
    model = User
    form_class = forms.UserUpdateForm
    template_name = "accounts/user_form.html"

    def get_queryset(self):
        return super().get_queryset().filter(pk=self.kwargs.get("pk"))
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse("accounts:user_detail", kwargs={"pk": self.object.pk})
    
    def dispatch(self, request, *args, **kwargs):
        user = self.get_object()
        if request.user != user:
            raise Http404("You do not have the permission for this action!")
        return super().dispatch(request, *args, **kwargs)
    
class DeleteUser(LoginRequiredMixin, DeleteView):
    model = User
    template_name = "accounts/delete_user.html"
    success_url = reverse_lazy("home")

    def get_queryset(self):
        return super().get_queryset().filter(pk=self.kwargs.get("pk"))
    
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
    
    def dispatch(self, request, *args, **kwargs):
        if request.user != self.get_object():
            raise Http404("You don't have the permission to do that!")
        return super().dispatch(request, *args, **kwargs)