from django.shortcuts import render, redirect
from products.models import Category, Product, Box, Invitation, BoxItem
from cart.models import CartItem, Cart
from accounts.models import User
from django.views.generic import *
from django.contrib.auth import get_user_model
from braces.views import SelectRelatedMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from products import forms
from reviews.forms import ProductReviewForm
from django.urls import reverse_lazy, reverse
from django.http import Http404, JsonResponse
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.core.cache import cache
import base64
from django.contrib import messages
import requests
from view_breadcrumbs import ListBreadcrumbMixin
from fuzzywuzzy import fuzz
import json
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from itertools import zip_longest
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from itertools import chain

# Sources:
# - Fuzzy search: https://www.datacamp.com/tutorial/fuzzy-string-python
# - Nutritional information: https://platform.fatsecret.com/docs/guides/authentication/oauth2#:~:text=Making%20a%20request&text=Clients%20are%20allocated%20two%20pieces,for%20accessing%20FatSecret%20API%20resources.&text=Register%20an%20application%20and%20you,Client%20ID%20and%20Client%20Secret.
# - Disease information: https://github.com/flowerchecker/Plant-id-API/blob/master/python/health_assessment_example.py
# - json.loads(): https://docs.python.org/3/library/json.html
# - prefetch_related: https://www.geeksforgeeks.org/prefetch_related-and-select_related-functions-in-django/

"""
PRODUCT
Views for handeling product management:
    ProductList: list of the elements in the shop
    ProductDetail: details of a product
    CreateProduct: allows farmers to create a product
    DeleteProduct: allows farmers to delete their product
    UpdateProduct: allows farmers to update their product
"""

# used in the views to get for each product the quantity in cart
# to update the add to cart buttons
def get_cart_quantities(user, products):
        q = []
        # user must be authenticated to have products in cart
        if user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=user)
            for product in products:
                try:
                    # get the correct model (Product or Box)
                    content_type = ContentType.objects.get_for_model(product)
                    object_id = product.pk
                    # get the cart item
                    cart_item = cart.cartitem_set.get(content_type=content_type, object_id=object_id)
                    # append the cart item quantity to q
                    q.append(cart_item.quantity)
                except CartItem.DoesNotExist:
                    # if it does not exist it means that it's not in the cart so quantity = 0
                    q.append(0)
        else:
            # is user is not authenticated all the quantities are 0
            for product in products:
                q.append(0)
        return q

class ProductList(ListBreadcrumbMixin, ListView):
    model = Product
    template_name = "products/product_list.html"
    context_object_name = "products"        
    
    # here happens the search and filtering logic
    def get_queryset(self):
        query = self.request.GET.get("q")
        farmer_id = self.kwargs.get("pk")
        category = self.request.GET.get("category")
        sort_by = self.request.GET.get("sort_by")
        # check if the user requested search or filtering
        if query:
            return self.get_products_by_search(query)
        elif category:
            queryset = self.get_products_by_category(category)
        elif farmer_id:
            return self.get_products_by_farmer(farmer_id)
        else:
            queryset = self.get_all_products()
        # extract the products and boxes from queryset
        products = queryset.get("products")
        boxes = queryset.get("boxes")
        # sort the products and boxes if necessary
        if products:
            if sort_by == "ascending":
                products = products.order_by("price")
            elif sort_by == "descending":
                products = products.order_by("-price")
            elif sort_by == "best_rated":
                products = products.order_by("-avg_rating")  
        if boxes:
            if sort_by == "ascending":
                boxes = boxes.order_by("price")
            elif sort_by == "descending":
                boxes = boxes.order_by("-price")
            elif sort_by == "best_rated":
                boxes = boxes.order_by("-avg_rating")             
        # give each product its quantity in the cart (for rendering)
        products = zip_longest(products, get_cart_quantities(self.request.user, products))    
        requestes_products = {"products": products, "boxes": boxes}
        return requestes_products
        
    def get_products_by_farmer(self, farmer_id):
        farmer = get_object_or_404(User, pk=farmer_id)
        # filter the products and boxes to get the the ones of a specific farmer
        products = Product.objects.filter(seller=farmer)
        boxes = Box.objects.filter(Q(asker=farmer) | Q(farmers=farmer))
        farmer_products = zip_longest(products, get_cart_quantities(self.request.user, products))
        return {"products": farmer_products, "boxes": boxes}
    
    def get_products_by_category(self, category):
        # get the products that have the category in their categories
        products = Product.objects.filter(categories__name__iexact=category)
        boxes = Box.objects.all()
        if category.lower() != "box":
            return {"products": products}
        else: 
            return {"products": products, "boxes": boxes}
    
    def get_products_by_search(self, search):
        ratio = 60
        products = Product.objects.all()
        box_items = BoxItem.objects.all()
        # use token sort because it doesn't care in what order, it accounts for similar strings
        product_search_result = [
            product for product in products
            if fuzz.token_sort_ratio(search, product.name) >= ratio # product name
                or fuzz.token_sort_ratio(search, product.seller) >= ratio # seller
                  or fuzz.token_sort_ratio(search, product.description) >= ratio # product description
        ]
        box_search_result = [
            box_item.box for box_item in box_items
            if fuzz.token_sort_ratio(search, box_item.box.name) >= ratio # box name
                or fuzz.token_sort_ratio(search, box_item.box.asker) >= ratio # asker
                  or fuzz.token_sort_ratio(search, box_item.box.description) >= ratio # box description
                  or fuzz.token_sort_ratio(search, box_item.product.name) >= ratio # box items
        ]
        # get quantity for each product (for rendering)
        product_search_result = zip_longest(product_search_result, get_cart_quantities(self.request.user, product_search_result)) 
        return {"products": product_search_result, "boxes": box_search_result}
    
    def get_all_products(self):
        if self.request.user.is_authenticated:
            # find the favorite pk's strings by using cookies
            fav_ids_str = self.request.COOKIES.get("fav", "[]")
            # turn these strings into integer using json.loads()
            fav_ids = [int(pk) for pk in json.loads(fav_ids_str)]
            # filter products and boxes of favorite farmers
            fav_boxes = Box.objects.filter(asker__pk__in=fav_ids)
            other_boxes = Box.objects.exclude(asker__pk__in=fav_ids)
            res_boxes = fav_boxes | other_boxes
            fav_products = Product.objects.filter(seller__pk__in=fav_ids)
            other_products = Product.objects.exclude(seller__pk__in=fav_ids)
            # assign to each product an idx to sort them because the query-append "|" doesn't hold the order
            fav_products_with_sort = [(1, product) for product in fav_products]
            other_products_with_sort = [(2, product) for product in other_products]
            res_products_with_sort = sorted(chain(fav_products_with_sort, other_products_with_sort), key=lambda x: x[0])
            res_products = [product for _, product in res_products_with_sort]
            return {"products": res_products, "boxes": res_boxes}
        # if user is not authenticated he can't have favorite farmers
        products = Product.objects.all()
        boxes = Box.objects.all()
        return {"products": products, "boxes": boxes}
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # add categories to context to render for filtering
        context["categories"] = Category.objects.all()
        return context
    
class ProductDetail(DetailView):
    model = Product
    template_name = "products/product_detail.html"
    form_class = ProductReviewForm

    def get_queryset(self):
        # get also the reviews of a product
        return super().get_queryset().prefetch_related("review_set")
    
    # get access_token to be able to make a request to FATSECRET api
    def get_access_token(self):
        client_id = settings.FATSECRET_CLIENT_ID
        client_secret = settings.FATSECRET_CLIENT_SECRET
        token_url = "https://oauth.fatsecret.com/connect/token"
        data = {
            "grant_type": "client_credentials",
            "scope": "basic"
        }
        headers = {
            "Authorization": "Basic " + base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode('utf-8')
        }
        # check if the access token is available in the cache
        cached_token = cache.get("access_token")
        if cached_token:
            return cached_token
        # otherwwise request an access token
        response = requests.post(token_url, data=data, headers=headers)
        if response.ok:
            access_data = response.json()
            access_token = access_data.get("access_token")
            expires_in = access_data.get("expires_in")
            # each access token has an expires_in field so cache the token
            # with a timeout equal to this field
            if access_token and expires_in:
                cache.set("access_token", access_token, timeout=expires_in)
                return access_token
        else: None

    def get_product_id(self, pk, access_token):
        product = Product.objects.get(pk=pk)
            # construct the url and headers
        api_url = f"https://platform.fatsecret.com/rest/server.api?method=foods.search&search_expression={product.name}&format=json"
        headers = {"Authorization": "Bearer " + access_token}
        response = requests.get(api_url, headers=headers)
        if response.ok:
            data = response.json()
            product_list = data.get("foods", {}).get("food", [])
            return product_list[0].get("food_id")
        return None

    def process_nutritional_info(self, info):
        processed_info = {}
        items = info.items()
        for key, value in items:
            #  don't add information that we don't need
            if key in ["is_default", "serving_url", "measurement_description", "metric_serving_amount", "metric_serving_unit", "serving_id"]:
                continue
            elif key == "serving_description":
                serving = value
                continue
            label = key.replace("_", " ").capitalize()
            processed_info[label] = value
        return (serving, processed_info)

    def get_nutritional_info(self, product_id, access_token):
        api_url = f"https://platform.fatsecret.com/rest/server.api?method=food.get.v3&food_id={product_id}&format=json"
        headers = {"Authorization": "Bearer " + access_token}
        # make a request to get the nutritional information
        response = requests.get(api_url, headers=headers)
        if response.ok:
            data = response.json()
            nutritional_info = data.get("food").get("servings", {}).get("serving", [])[0]
            # process the data to only get the features that we need
            return self.process_nutritional_info(nutritional_info)
        else: ()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = context["product"]
        context["review_type"] = "product"
        # get the access token
        access_token = self.get_access_token()
        if access_token:
            # if you got an access_token search the fatsecret id by looking in the database or making a request to fatsecret api
            product_id = self.get_product_id(product.pk, access_token)
            if product_id:
                # if you got the id get the nutritional info by making a request to the same api
                nutritional_info = self.get_nutritional_info(product_id, access_token)
                # add these information to the context for rendering
                context["serving"] = nutritional_info[0]
                context["nutritional_info"] = nutritional_info[1]
        # paginate the reviews by using django paginator
        reviews = product.review_set.all()  
        paginator = Paginator(reviews, 5)   
        page = self.request.GET.get("page")  
        try:
            paginated_reviews = paginator.page(page)
        except PageNotAnInteger:
            paginated_reviews = paginator.page(1)
        except EmptyPage:
            paginated_reviews = paginator.page(paginator.num_pages)
        # also add these informations to context for rendering
        context["quantity"] = get_cart_quantities(self.request.user, [product])[0]
        context["reviews"] = paginated_reviews       
        return context          
    
class CreateProduct(LoginRequiredMixin, CreateView):
    form_class = forms.ProductCreationForm
    model = Product
    template_name = "products/product_form.html"
    login_url = "accounts:login"

    def form_valid(self, form):
        self.object = form.save(commit=False)
        user_instance = User.objects.get(pk=self.request.user.pk)
        # add the user to the products seller
        self.object.seller = user_instance
        # save to database
        self.object.save()
        # notify the farmer for successfull creation
        messages.success(self.request, 'Product created successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("products:product_detail", kwargs={"pk": self.object.pk})
    
    def dispatch(self, request, *args, **kwargs):
        # if the user is not a farmer he can't create products so deny access
        if not request.user.is_farmer:
            # notify user for error and redirect to home page
            messages.error(request, "You don't have the permissions to create a product!")
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)
    

class DeleteProduct(LoginRequiredMixin, DeleteView):
    model = Product
    success_url = reverse_lazy("products:product_list")
    template_name = "products/confirm_delete.html"
    login_url = "accounts:login"

    def get_queryset(self):
        return super().get_queryset().filter(pk=self.kwargs.get("pk"))

    def delete(self, *args, **kwargs):
        product = self.get_object()
        # if the user is not the seller of the product he can't delete it
        if self.request.user != product.seller:
            messages.error(self.request, "You don't have the permissions to delete this product!")
            return redirect("home")
        return super().delete(*args, **kwargs)
    
    def dispatch(self, request, *args, **kwargs):
        # if the user is not a farmer he can't create products so deny access
        if not request.user.is_farmer:
            # notify user for error and redirect to home page
            messages.error(request, "You don't have the permissions to delete a product!")
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)
    
class UpdateProduct(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = forms.ProductCreationForm
    template_name = "products/product_form.html"

    def get_queryset(self):
        # return the correct product
        return super().get_queryset().filter(pk=self.kwargs.get("pk"))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # the form for creating and updating is the same so add a variable to know if you are adding or updating
        context["is_update"] = True
        return context
    
    def get_success_url(self):
        # after a successfull update send the user to the detail page
        return reverse("products:product_detail", kwargs={"pk": self.object.pk})
    
    def dispatch(self, request, *args, **kwargs):
        product = self.get_object()
        if request.user != product.seller:
            messages.error(self.request, "You don't have the permissions to update this product!")
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)
    
"""
BOX
Views for handeling box management:
    CreateBox: handles the creation of a bpx
    BoxDetail: handles the detailed view of a box
    PendingBoxList: handles the view of the boxes list
    PendingDecision: handles the decision making process of boxes
    AddProductToBox: handles the addition of products to boxes
"""

class CreateBox(CreateView):
    model = Box
    template_name = 'products/box_form.html'
    form_class = forms.BoxCreationForm
    success_url = reverse_lazy("products:pending") # send the user to the list of boxes after a succesfull creation

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            # if request is POST create the formset with the data from the form
            formset = forms.BoxItemFormSet(self.request.POST, instance=self.object, prefix='boxitem')
        else:
            # else initialize the formset woth existing data
            formset = forms.BoxItemFormSet(instance=self.object, prefix='boxitem')
        #add formset to context for rendering
        context['formset'] = formset
        return context
    
    def send_invitations(self):
        # create an invitation for each invited farmer
        invited_farmers = self.object.farmers.all()
        for farmer in invited_farmers:
            Invitation.objects.create(
                inviting_farmer = self.request.user,
                invited_farmer = farmer,
                box = self.object
            )

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if form.is_valid() and formset.is_valid():
            self.object = form.save(commit=False)
            self.object.asker = self.request.user
            self.object.save()
            self.object.farmers.set(form.cleaned_data.get('farmers', []))
            formset.instance = self.object
            # for each form from the formset create a boxitem with the given data
            for form in formset.forms:
                product = form.cleaned_data.get('product')
                quantity = form.cleaned_data.get('quantity')
                BoxItem.objects.create(box=self.object, product=product, quantity=quantity)
            # send the invitations to the selected farmers
            self.send_invitations()
            # notify the user that the box was created
            messages.success(self.request, 'Box created successfully!')
            return redirect(self.success_url)
        return self.form_invalid(form)
        
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # add user to the kwargs to be able to exlude him from the farmers selection list
        kwargs["user"] = self.request.user
        return kwargs


class BoxDetail(DetailView):
    model = Box
    template_name = "products/box_detail.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        box = self.object
        # can_add is to check if the farmer can still add a product or not 
        can_add = True if self.request.user == box.asker or Invitation.objects.filter(box=box, invited_farmer=self.request.user).exists() and Invitation.objects.get(box=box, invited_farmer=self.request.user).status == "accepted" else False
        box_items = box.items.all()
        # farmers_product are the products that the farmer can still add so:
        # get all the products of the farmer
        farmers_product = Product.objects.filter(seller=self.request.user)
        # remove all the products that are already in the box
        farmers_product = farmers_product.exclude(pk__in=box_items.values_list("product__pk", flat=True))
        invitations = Invitation.objects.filter(box=box)
        # add all these informations to context for rendering
        context["products"] = box_items
        context["farmers_products"] = farmers_product
        context["invitations"] = invitations
        context["can_add"] = can_add
        return context

class PendingBoxList(ListView):
    model = Box
    template_name = "products/pending_list.html"
    context_object_name = "pending_boxes"

    def get_queryset(self):
        user = self.request.user
        # only the staff can see the pending boxes (they need to approve or reject the box)
        if user.is_staff:
            pending_boxes = Box.objects.filter(status="pending")
            confirmed_boxes = [box for box in pending_boxes if box.is_confirmed()]
            return confirmed_boxes
        else: return None   

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        # for the farmers show the boxes and invitations to join boxes
        if user.is_farmer:
            boxes = Box.objects.filter(Q(asker=user) | Q(farmers__in=[user]))
            invitations = {}
            for box in boxes:
                if user == box.asker:
                    # the asker of a box didn't receive a invitation because he's the creator
                    if box not in invitations:
                        invitations[box] = {"box": box, "invitation": []}
                elif box.farmers.filter(pk=user.pk).exists():
                    # other invited farmers received an invitation
                    invitation = Invitation.objects.get(invited_farmer=user, box=box)
                    if box not in invitations:
                        invitations[box] = {"box": box, "invitation": invitation}
            # get only the values not the keys
            invitations = invitations.values()
            context["invitations"] = invitations
            return context

class PendingDecision(View):
    def post(self, request, *args, **kwargs):
        box_id = self.kwargs.get("pk")
        action = request.POST.get("action")
        user = request.user
        # staff members approve or reject box creation requests
        if user.is_staff:
            try:
                box = Box.objects.get(pk=box_id)
                if action == "approve":
                    box.status = "approved"
                    box.save()
                elif action == "reject":
                    box.status = "rejected"
                    box.save()
            except Box.DoesNotExist:
                messages.error(self.request, "There was an error: box does not exist!")
                return redirect("home")
        # the farmers can accept or reject
        if user.is_farmer:
            try: 
                box = Box.objects.get(pk=box_id)
                if user != box.asker:
                    invitation = Invitation.objects.get(invited_farmer=user, box=box)
                if action == "accept":
                    invitation.status = "accepted"
                    invitation.decision_date = timezone.now()
                    invitation.save()
                elif action == "reject":
                    invitation.status = "rejected"
                    invitation.decision_date = timezone.now()
                    # when farmer rejected invitation remove from invited farmers
                    box.farmers.remove(user)
                    box.save()
                    invitation.save() 
                elif action == "confirm":
                    # when confirming add the farmer to the list of confirmed (farmers who confirmed the box)
                    box.confirmed.add(user)
                    box.save()
            except Box.DoesNotExist:
                messages.error(self.request, "There was an error: box does not exist!")
                return redirect("home")

        return redirect("products:pending")  
    
class AddProductToBox(UpdateView):
    model = Box
    template_name = "products/box_detail.html"
    fields = []

    def get_success_url(self):
        return reverse_lazy("products:box_detail", kwargs={"pk": self.kwargs.get("pk")})
    
    def post(self, request, *args, **kwargs):
        try:
            # get the data from the request
            data = json.loads(request.body)
            selected_products = data.get("selected_products")
            box = self.get_object()
            if selected_products:
                for item in selected_products:
                    # extract for each selected element the pk of the product and the quantity
                    product_pk = item.get("product")
                    quantity = item.get("quantity")
                    if product_pk and quantity:
                        # get the product and create a box item
                        product = Product.objects.get(pk=product_pk)
                        box_item, created = BoxItem.objects.get_or_create(
                            box=box,
                            product=product,
                        )
                        if not created:
                            # if box item already existed just update quantity
                            box_item.quantity += quantity
                        # save to database
                        box_item.save()
                box.save()
            # return a successsfull status
            return JsonResponse({"status": "success"})
        except Exception as e:
            # else notify the user of the error
            messages.error(self.request, f"There was an error: {str(e)}")
            return redirect("home")
    
"""
    PLANT INFORMATION
"""
class IdentifyDisease(TemplateView):
    template_name = "products/identify_disease.html"

    def post(self, request, *args, **kwargs):
        # construct the url and ask some more information (local name, description and treatment)
        api_url = "https://plant.id/api/v3/health_assessment?details=local_name,description,treatment"
        api_key = settings.PLANT_ID_API_KEY
        # get the users position for better identification of disease
        latitude = float(request.POST.get("latitude", 0))
        longitude = float(request.POST.get("longitude", 0))
        similar_images = True # get similar images
        # construct the data to send to the api
        data = {
            'latitude': latitude,
            'longitude': longitude,
            'similar_images': similar_images,
            'health': "only",
        }
        headers = {
            'Api-Key': api_key,
        }
        files = {'images': request.FILES.get("image")}
        # send the request with data and image
        response = requests.post(api_url, data=data, files=files, headers=headers)
        if response.status_code == 201:
            # if you get a successfull response add data to context to render on the correct page
            result = response.json()
            return render(request, "products/disease_info.html", {"data": result})
        else:
            # else show an error message
            messages.error(self.request, "Error getting the disease informations")
            return redirect("home")

        
class DiseaseInfo(TemplateView):
    # render the received data to template
    template_name = "products/disease_info.html"
    
"""
    ViewSet for managing different products
"""   
from rest_framework import viewsets, permissions
from .serializers import ProductSerializer, BoxSerializer

class IsSellerOrFarmer(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.method == "POST": # create a product only possible for farmers
            return request.user.is_farmer
        return obj.seller == request.user # updating and deleting only possible for the seller or the product
    
class IsStaff(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff # all the box operations only available for staff members

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer    
    permission_classes = [permissions.IsAuthenticated, IsSellerOrFarmer]

class BoxViewSet(viewsets.ModelViewSet):
    queryset = Box.objects.all()
    serializer_class = BoxSerializer  
    permission_classes = [permissions.IsAuthenticated, IsStaff]
    

    