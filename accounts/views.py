from django.urls import reverse_lazy, reverse
from django.views.generic import View, CreateView, ListView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, JsonResponse
from .models import User
from view_breadcrumbs import ListBreadcrumbMixin, DetailBreadcrumbMixin
from . import forms

# Souces: 
# - Breadcrumbs: https://pypi.org/project/django-view-breadcrumbs/

"""
    Views for handling different aspects of user management:
        SingUp: handles user registration
        UserDetail: shows detailed information about a user
        FarmerList: lists the farmers
        UpdateUser: allows users to update their profile information
        DeleteUser: allows users to delete their account
"""

class SignUp(CreateView):
    # form to be used for registration
    form_class = forms.UserSignUpForm
    # after a successfull registration redirects user to the login page
    success_url = reverse_lazy("login")
    # template for rendering
    template_name = "accounts/signup.html"

class UserDetail(DetailBreadcrumbMixin, DetailView):
    # used model
    model = User
    template_name = "accounts/user_detail.html"
    # set the name of the variable containing the user details
    context_object_name = "user_detail"

    # prefetch the farmer reviews to reduce the number of database queries
    def get_queryset(self):
        return super().get_queryset().prefetch_related("farmer_reviews")
    
    # add the reviews to the context to be able to render them
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        farmer = context["user_detail"]
        context["reviews"] = farmer.farmer_reviews.all()
        return context

class FarmerList(ListBreadcrumbMixin, ListView):
    model = User
    template_name = "accounts/farmers_list.html"
    context_object_name = "farmers"

    def get_queryset(self):
        # return only the users that are farmers
        return User.objects.filter(is_farmer=True)
    
    def post(self, request, *args, **kwargs):
        farmers = self.get_queryset().values("username", "latitude", "longitude")
        my_location = (self.request.user.longitude, self.request.user.latitude)
        # return a JSON response with the farmers and the user's location
        return JsonResponse({"farmers": list(farmers), "location": my_location}, safe=False)
    
#use LoginRequiredMixin to ensure that only authenticated users can access this view
class UpdateUser(LoginRequiredMixin, UpdateView):
    model = User
    form_class = forms.UserUpdateForm
    template_name = "accounts/user_form.html"
    
    def form_valid(self, form):
        # save the form to the object without updating the database
        self.object = form.save(commit=False)
        # save the object to the database
        self.object.save()
        return super().form_valid(form)
    
    # after successfully updating redirect to user detail page
    def get_success_url(self):
        return reverse("accounts:user_detail", kwargs={"pk": self.object.pk})
    
    def dispatch(self, request, *args, **kwargs):
        # the view fetches the correct object
        if request.user != self.object:
            raise Http404("You do not have the permission for this action!")
        return super().dispatch(request, *args, **kwargs)
    
class DeleteUser(LoginRequiredMixin, DeleteView):
    model = User
    template_name = "accounts/delete_user.html"
    success_url = reverse_lazy("home")
    
    def dispatch(self, request, *args, **kwargs):
        # if the user is not allowed to delete raise an error
        if request.user != self.get_object():
            raise Http404("You don't have the permission to do that!")
        return super().dispatch(request, *args, **kwargs)
    
class CheckUsername(View):
    def get(self, request, *args, **kwargs):
        username = self.request.GET.get("username")
        if username:
            available = User.objects.filter(username__iexact=username).exists()
            return JsonResponse({"available": available})
        