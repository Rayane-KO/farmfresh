from django.urls import reverse_lazy, reverse
from django.views.generic import *
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, JsonResponse
from .models import User
from view_breadcrumbs import ListBreadcrumbMixin, DetailBreadcrumbMixin
from . import forms
from products.models import Product, Box
from orders.models import Order, OrderItem
from geopy.distance import great_circle
from django.core.mail import EmailMessage
from django.db.models import Sum, Avg, Count, Q
from reviews.models import FarmerReview, ProductReview
import json
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import redirect

# Souces: 
# - Breadcrumbs: https://pypi.org/project/django-view-breadcrumbs/
# - Pagination: https://docs.djangoproject.com/fr/2.1/topics/pagination/
# - ViewSets: https://www.django-rest-framework.org/api-guide/viewsets/
# - ContentType: https://docs.djangoproject.com/en/5.0/ref/contrib/contenttypes/

"""
Views for handling different aspects of user management:
    SingUp: handles user registration
    UserDetail: shows detailed information about a user
    FarmerList: lists the farmers
    UpdateUser: allows users to update their profile information
    DeleteUser: allows users to delete their account
    CheckUsername: client-side validation of username
    Dashboard: allows farmers to see a dashboard of their sales
"""

class SignUp(CreateView):
    # form to be used for registration
    form_class = forms.UserSignUpForm
    # after a successfull registration redirects user to the login page
    success_url = reverse_lazy("login")
    # template for rendering
    template_name = "accounts/signup.html"

class UserDetail(LoginRequiredMixin, DetailBreadcrumbMixin, DetailView):
    # used model
    model = User
    template_name = "accounts/user_detail.html"
    # set the name of the variable containing the user details
    context_object_name = "user_detail"
    # redirect user if not logged in
    login_url="accounts:login"

    # prefetch the farmer reviews to reduce the number of database queries
    def get_queryset(self):
        return super().get_queryset().prefetch_related("farmer_reviews")
    
    # add the reviews to the context to be able to render them
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        farmer = context["user_detail"]
        context["review_type"] = "farmer"
        reviews = farmer.farmer_reviews.all().order_by("-date")
        # paginate the reviews with 5 reviews per page
        paginator = Paginator(reviews, 5)   
        page = self.request.GET.get("page")  
        try:
            paginated_reviews = paginator.page(page)
        except PageNotAnInteger:
            paginated_reviews = paginator.page(1)
        except EmptyPage:
            paginated_reviews = paginator.page(paginator.num_pages)
        # add the reviews to the context
        context["reviews"] = paginated_reviews       
        return context  

# use LoginRequiredMixin to ensure that only logged-in users can access the page
class FarmerList(LoginRequiredMixin, ListBreadcrumbMixin, ListView):
    model = User
    template_name = "accounts/farmers_list.html"
    context_object_name = "farmers"
    login_url="accounts:login"

    def get_queryset(self):
        # get the parameters of the query
        closest_farmers = self.request.GET.get("closest_farmers")
        best_farmers = self.request.GET.get("best_farmers")
        fav_farmers = self.request.GET.get("fav_farmers")
        farmers = User.objects.filter(is_farmer=True) # all the farmers
        # apply the correct filtering specified in the parameters of the query
        if closest_farmers:
            return self.get_closest_farmers()
        elif best_farmers:
            return self.get_best_farmers()
        elif fav_farmers:
            return self.get_fav_farmers()
        else: 
            return farmers

    # filter the farmers by distance
    def get_closest_farmers(self):
        # get only the farmers that have a location
        farmers = User.objects.filter(is_farmer=True).exclude(latitude__isnull=True, longitude__isnull=True)
        # get the location of the logged-in user
        my_location = (self.request.user.longitude, self.request.user.latitude)
        # use the great_circle function from geopy to calculate the distance between locations
        # and sort with minimum distance
        farmers = sorted(
            farmers,
            key=lambda farmer: great_circle((farmer.longitude, farmer.latitude), my_location).miles
        )
        return farmers
    
    # filter the farmers by rating
    def get_best_farmers(self):
        # get all the farmers
        farmers = User.objects.filter(is_farmer=True)
        # order the farmers from high to low avg_rating
        return farmers.order_by("-avg_rating")
    
    def get_fav_farmers(self):
        # get the favorite farmers from localStorage in cookie
        fav_ids_str = self.request.COOKIES.get("fav", [])
        # change each string number into an integer
        fav_ids = [int(fav_id.strip('"')) for fav_id in fav_ids_str.strip("[").strip("]").split(",")] if fav_ids_str else []
        # get the farmers that are in the favorite list
        farmers = User.objects.filter(pk__in=fav_ids) if fav_ids else User.objects.all()
        return farmers
    
    def post(self, request, *args, **kwargs):
        farmers = self.get_queryset().values("username", "pk", "latitude", "longitude")
        longitude = request.user.longitude
        latitude = request.user.latitude
        if latitude is None or longitude is None:
            # if location is not available ask user to fill the rest of the form
            redirect(reverse("accounts:user_detail", kwargs={"pk": request.user.pk}))
        else:
            my_location = (self.request.user.longitude, self.request.user.latitude)
        # return a JSON response with the farmers and the user's location
        return JsonResponse({"farmers": list(farmers), "location": my_location}, safe=False)
    
class UpdateUser(LoginRequiredMixin, UpdateView):
    model = User
    form_class = forms.UserUpdateForm # form to use to update user
    template_name = "accounts/user_form.html"
    
    def form_valid(self, form):
        # save the object to the database
        self.object = form.save()
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
    success_url = reverse_lazy("home") # when user is deleted, redirect to home
    
    def dispatch(self, request, *args, **kwargs):
        # if the user is not allowed to delete raise an error
        if request.user != self.get_object():
            raise Http404("You don't have the permission for this action!")
        return super().dispatch(request, *args, **kwargs)
    
class CheckUsername(View):
    def get(self, request, *args, **kwargs):
        username = self.request.GET.get("username")
        if username:
            # check if the username is available by checking if there exist a user with this username
            available = not User.objects.filter(username__iexact=username).exists()
            return JsonResponse({"available": available})

class Dashboard(TemplateView):
    template_name = "accounts/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        farmer = self.request.user
        # get the sold products from the farmer
        product_items = OrderItem.objects.filter(
            content_type__model='product',
            object_id__in=Product.objects.filter(seller=farmer).values('pk')
        )
        # get the sold products from farmers from boxes
        box_items = OrderItem.objects.filter(
            content_type__model='box',
            object_id__in=Box.objects.filter(asker=farmer).values('pk')
        )
        # add all the products together
        product_items = product_items | box_items 
        # annotate each order date with the total sales
        sales = product_items.values("order__order_date").annotate(total_sales=Sum("total"))
        # data to be used for the chart
        data = {
            "labels": [sale["order__order_date"].strftime("%B %Y") for sale in sales], # convert order date to "Month Year"
            "data": [float(sale["total_sales"]) for sale in sales], # data for the chart
        }
        # get the 5 most purchased products
        products_quantity = Product.objects.filter(seller=farmer).annotate(total_quantity=Sum('order_items__quantity'))
        top_products = products_quantity.order_by('-total_quantity')[:5]
        # get the recent orders (5)
        recent_orders = product_items.order_by('-order__order_date')[:5]
        # for each product of the farmer add information about sales, rating and reviews
        product_performance = Product.objects.filter(seller=farmer).annotate(
            total_sales=Sum('order_items__quantity'),
            average_rating=Avg('review_set__rating'), # fields can't have the same names as the fields in models otherwise it will conflict
            review_count=Count('review_set'),
        )
        # get recent reviews (5)
        customer_feedback = ProductReview.objects.filter(product__seller=farmer).order_by('-date')[:5]
        # add all the information to the context to be able to render them on the html page
        context["farmer"] = farmer
        context["data"] = data
        context["top_products"] = top_products
        context["recent_orders"] = recent_orders
        context["product_performance"] = product_performance
        context["customer_feedback"] = customer_feedback
        return context

# Source:
#   - customized permissions: https://www.django-rest-framework.org/api-guide/permissions/#:~:text=The%20default%20permission%20policy%20may,For%20example.&text=You%20can%20also%20set%20the,the%20APIView%20class%2Dbased%20views.&text=Or%2C%20if%20you're%20using,decorator%20with%20function%20based%20views.

"""
    Serializer View
"""   
from rest_framework import viewsets, permissions
from .serializers import FarmerSerializer

class IsFarmer(permissions.BasePermission):
    # customized permission
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj == request.user # for updating and deleting, it can only be done by users himself

class FarmerViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(is_farmer=True)
    serializer_class = FarmerSerializer    
    permission_classes = [permissions.IsAuthenticated, IsFarmer] # only authenticated users can access information, but modifying is for the owner of the account