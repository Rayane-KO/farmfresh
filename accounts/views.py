from django.urls import reverse_lazy, reverse
from django.views.generic import View, CreateView, ListView, DetailView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, JsonResponse
from .models import User
from view_breadcrumbs import ListBreadcrumbMixin, DetailBreadcrumbMixin
from . import forms
from products.models import Product
from orders.models import Order, OrderItem
from geopy.distance import great_circle
from django.core.mail import EmailMessage
from django.db.models import Sum, Avg, Count
from reviews.models import FarmerReview, ProductReview
import json
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

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
        context["review_type"] = "farmer"
        reviews = farmer.farmer_reviews.all()
        paginator = Paginator(reviews, 5)   
        page = self.request.GET.get("page")  
        try:
            paginated_reviews = paginator.page(page)
        except PageNotAnInteger:
            paginated_reviews = paginator.page(1)
        except EmptyPage:
            paginated_reviews = paginator.page(paginator.num_pages)
        context["reviews"] = paginated_reviews       
        return context  

class FarmerList(ListBreadcrumbMixin, ListView):
    model = User
    template_name = "accounts/farmers_list.html"
    context_object_name = "farmers"

    def get_queryset(self):
        closest_farmers = self.request.GET.get("closest_farmers")
        best_farmers = self.request.GET.get("best_farmers")
        fav_farmers = self.request.GET.get("fav_farmers")
        farmers = User.objects.filter(is_farmer=True)
        if closest_farmers:
            return self.get_closest_farmers()
        elif best_farmers:
            return self.get_best_farmers()
        elif fav_farmers:
            return self.get_fav_farmers()
        else: 
            return farmers

    def get_closest_farmers(self):
        farmers = User.objects.filter(is_farmer=True).exclude(latitude__isnull=True, longitude__isnull=True)
        my_location = (self.request.user.longitude, self.request.user.latitude)
        farmers = sorted(
            farmers,
            key=lambda farmer: great_circle((farmer.longitude, farmer.latitude), my_location).miles
        )
        return farmers
    
    def get_best_farmers(self):
        farmers = User.objects.filter(is_farmer=True)
        return farmers.order_by("-avg_rating")
    
    def get_fav_farmers(self):
        fav_ids_str = self.request.COOKIES.get("fav", "")
        fav_ids = [int(fav_id.strip('"')) for fav_id in fav_ids_str.strip("[").strip("]").split(",")] if fav_ids_str else []
        farmers = User.objects.filter(pk__in=fav_ids)
        print(farmers)
        return farmers
    
    def post(self, request, *args, **kwargs):
        farmers = self.get_queryset().values("username", "pk", "latitude", "longitude")
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
        if request.user != self.get_object():
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
        
class Dashboard(TemplateView):
    template_name = "accounts/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        farmer = self.request.user
        sales = OrderItem.objects.filter(
            product__seller=farmer
        ).values("order__order_date").annotate(total_sales=Sum("total"))

        data = {
            "labels": [sale["order__order_date"].strftime("%B %Y") for sale in sales],
            "data": [str(sale["total_sales"]) for sale in sales],
        }
        most_purchased_products = Product.objects.filter(orderitem__product__seller=farmer).annotate(total_quantity=Sum('orderitem__quantity')).order_by('-total_quantity')[:5]
        recent_orders = OrderItem.objects.filter(product__seller=farmer).order_by('-order__order_date')[:5]
        product_performance = Product.objects.filter(seller=farmer).annotate(
            total_sales=Sum('orderitem__quantity'),
            average_rating=Avg('review_set__rating'),
            review_count=Count('review_set'),
        )
        customer_feedback = ProductReview.objects.filter(product__seller=farmer).order_by('-date')[:5]
        context["farmer"] = farmer
        context["data"] = data
        context["top_products"] = most_purchased_products
        context["recent_orders"] = recent_orders
        context["product_performance"] = product_performance
        context["customer_feedback"] = customer_feedback
        return context

        