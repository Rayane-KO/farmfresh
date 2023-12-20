from typing import Any
from django import http
from django.shortcuts import render, redirect
from products.models import Category, Product, Box, Invitation, BoxItem
from cart.models import CartItem, Cart
from django.views.generic import View, ListView, DetailView, CreateView, DeleteView, UpdateView, TemplateView
from django.contrib.auth import get_user_model
from braces.views import SelectRelatedMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from products import forms
from reviews.forms import ProductReviewForm
from reviews.models import ProductReview
from django.urls import reverse_lazy, reverse
from django.http import Http404, JsonResponse
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.core.cache import cache
import base64
from django.contrib import messages
import requests
from view_breadcrumbs import ListBreadcrumbMixin, DetailBreadcrumbMixin
from fuzzywuzzy import fuzz
import json
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from itertools import zip_longest
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from itertools import chain

User = get_user_model()

# Sources:
# Fuzzy search: https://www.datacamp.com/tutorial/fuzzy-string-python

"""
    PRODUCT
"""
def get_cart_quantities(user, product_type, products):
        q = []
        if user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=user)
            for product in products:
                try:
                    content_type = ContentType.objects.get_for_model(product)
                    object_id = product.pk
                    cart_item = cart.cartitem_set.get(content_type=content_type, object_id=object_id)
                    q.append(cart_item.quantity)
                except CartItem.DoesNotExist:
                    q.append(0)
        else:
            for product in products:
                q.append(0)
        return q


class ProductList(ListBreadcrumbMixin, ListView):
    model = Product
    template_name = "products/product_list.html"
    context_object_name = "products"        
    
    def get_queryset(self):
        query = self.request.GET.get("q")
        farmer_id = self.kwargs.get("pk")
        category = self.request.GET.get("category")
        sort_by = self.request.GET.get("sort_by")
        if query:
            return self.get_products_by_search(query)
        elif category:
            queryset = self.get_products_by_category(category)
        elif farmer_id:
            return self.get_products_by_farmer(farmer_id)
        else:
            queryset = self.get_all_products()

        products = queryset.get("products")
        boxes = queryset.get("boxes")

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

        products = zip_longest(products, get_cart_quantities(self.request.user, "product", products))    
        requestes_products = {"products": products, "boxes": boxes}

        return requestes_products
        
    def get_products_by_farmer(self, farmer_id):
        # return the products of a specific farmer
        farmer = get_object_or_404(User, pk=farmer_id)
        products = Product.objects.filter(seller=farmer)
        boxes = Box.objects.filter(Q(asker=farmer) | Q(farmers=farmer))
        farmer_products = zip_longest(products, get_cart_quantities(self.request.user, "product", products))
        return {"products": farmer_products, "boxes": boxes}
    
    def get_products_by_category(self, category):
        products = Product.objects.filter(categories__name__iexact=category)
        boxes = Box.objects.all()
        if category.lower() != "box":
            return {"products": products}
        else: 
            return {"products": products, "boxes": boxes}
    
    def get_products_by_search(self, search):
        products = Product.objects.all()
        boxes = Box.objects.all()
        # use token sort because it doesn't care in what order, it accounts for similar strings
        product_search_result = [
            product for product in products
            if fuzz.token_sort_ratio(search, product.name) >= 70
                or fuzz.token_sort_ratio(search, product.seller) >= 70
                  or fuzz.token_sort_ratio(search, product.description) >= 70
        ]
        box_search_result = [
            box for box in boxes
            if fuzz.token_sort_ratio(search, box.name) >= 70
                or fuzz.token_sort_ratio(search, box.asker) >= 70
                  or fuzz.token_sort_ratio(search, box.description) >= 70
        ]
        product_search_result = zip_longest(product_search_result, get_cart_quantities(self.request.user, "product", product_search_result)) 
        return {"products": product_search_result, "boxes": box_search_result}
    
    def get_all_products(self):
        if self.request.user.is_authenticated:
            fav_ids_str = self.request.COOKIES.get("fav", "[]")
            if fav_ids_str != "null" or fav_ids_str == "[]" or fav_ids_str == []:
                fav_ids = [int(pk) for pk in json.loads(fav_ids_str)]
                fav_products = list(Product.objects.filter(seller__pk__in=fav_ids))
                other_products = list(Product.objects.exclude(seller__pk__in=fav_ids))
                fav_boxes = Box.objects.filter(asker__pk__in=fav_ids)
                other_boxes = Box.objects.exclude(asker__pk__in=fav_ids)
                res_products = fav_products + other_products
                res_boxes = fav_boxes | other_boxes
                fav_products = Product.objects.filter(seller__pk__in=fav_ids)
                other_products = Product.objects.exclude(seller__pk__in=fav_ids)

                # Add a custom sorting key to each queryset to preserve order
                fav_products_with_sort = [(1, product) for product in fav_products]
                other_products_with_sort = [(2, product) for product in other_products]

                # Concatenate the lists while maintaining the specified order
                res_products_with_sort = sorted(chain(fav_products_with_sort, other_products_with_sort), key=lambda x: x[0])

                # Extract the actual products from the result
                res_products = [product for _, product in res_products_with_sort]
                return {"products": res_products, "boxes": res_boxes}
            
            products = Product.objects.all()
            boxes = Box.objects.all()
            return {"products": products, "boxes": boxes}
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = Product.objects.all()

        context["categories"] = Category.objects.all()
        return context
    
    
    
class ProductDetail(SelectRelatedMixin, DetailView):
    model = Product
    select_related = ("seller",)
    template_name = "products/product_detail.html"
    form_class = ProductReviewForm

    def get_queryset(self):
        return super().get_queryset().prefetch_related("review_set")
    
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
        if product.fatsecret_id:
            return product.fatsecret_id
        else:
            api_url = f"https://platform.fatsecret.com/rest/server.api?method=foods.search&search_expression={product.name}&format=json"
            headers = {"Authorization": "Bearer " + access_token}
            response = requests.get(api_url, headers=headers)
            if response.ok:
                data = response.json()
                product_list = data.get("foods", {}).get("food", [])
                if product_list:
                    product.fatsecret_id = product_list[0].get("food_id")
                    product.save()
                    return product.fatsecret_id
                else: return None
            else: return None

    def process_nutritional_info(self, info):
        processed_info = {}
        items = info.items()
        serving = ""
        for key, value in items:
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
        response = requests.get(api_url, headers=headers)
        if response.ok:
            data = response.json()
            nutritional_info = data.get("food").get("servings", {}).get("serving", [])[0]
            return self.process_nutritional_info(nutritional_info)
        else: ()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = context["product"]
        context["review_type"] = "product"
        access_token = self.get_access_token()
        if access_token:
            product_id = self.get_product_id(product.pk, access_token)
            #if product_id:
                #nutritional_info = self.get_nutritional_info(product_id, access_token)
                #context["serving"] = nutritional_info[0]
                #context["nutritional_info"] = nutritional_info[1]
        reviews = product.review_set.all()  
        paginator = Paginator(reviews, 5)   
        page = self.request.GET.get("page")  
        try:
            paginated_reviews = paginator.page(page)
        except PageNotAnInteger:
            paginated_reviews = paginator.page(1)
        except EmptyPage:
            paginated_reviews = paginator.page(paginator.num_pages)
        context["quantity"] = get_cart_quantities(self.request.user, "product", [product])[0]
        context["reviews"] = paginated_reviews       
        return context          
    
class CreateProduct(SelectRelatedMixin, LoginRequiredMixin, CreateView):
    form_class = forms.ProductCreationForm
    model = Product
    template_name = "products/product_form.html"

    def form_valid(self, form):
        self.object = form.save(commit=False)
        user_instance = User.objects.get(pk=self.request.user.pk)
        self.object.seller = user_instance
        self.object.save()
        messages.success(self.request, 'Product created successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("products:product_detail", kwargs={"pk": self.object.pk})
    

class DeleteProduct(LoginRequiredMixin, DeleteView):
    model = Product
    success_url = reverse_lazy("products:product_list")
    template_name = "products/confirm_delete.html"

    def get_queryset(self):
        return super().get_queryset().filter(pk=self.kwargs.get("pk"))

    def delete(self, *args, **kwargs):
        product = self.get_object()
        if self.request.user != product.seller:
            raise Http404("You don't Have the permissions")
        return super().delete(*args, **kwargs)
    
class UpdateProduct(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = forms.ProductCreationForm
    template_name = "products/product_form.html"

    def get_queryset(self):
        return super().get_queryset().filter(pk=self.kwargs.get("pk"))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_update"] = True
        return context
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse("products:product_detail", kwargs={"pk": self.object.pk})
    
    def dispatch(self, request, *args, **kwargs):
        product = self.get_object()
        if request.user != product.seller:
            raise Http404("You do not have the permission for this action!")
        return super().dispatch(request, *args, **kwargs)
    
"""
    BOX
"""

class CreateBox(CreateView):
    model = Box
    template_name = 'products/box_form.html'
    form_class = forms.BoxCreationForm
    success_url = reverse_lazy("products:pending")

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            formset = forms.BoxItemFormSet(self.request.POST, instance=self.object, prefix='boxitem')
        else:
            formset = forms.BoxItemFormSet(instance=self.object, prefix='boxitem')

        # Set the user attribute for the formset
        formset.user = self.request.user

        data['formset'] = formset
        return data
    
    def send_invitations(self):
        invited_farmers = self.object.farmers.all()
        print(invited_farmers)
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

            # Loop through forms in the formset to create BoxItem instances
            for form in formset.forms:
                product = form.cleaned_data.get('product')
                quantity = form.cleaned_data.get('quantity')

                if product and quantity:
                    BoxItem.objects.create(box=self.object, product=product, quantity=quantity)
            self.send_invitations()
            messages.success(self.request, 'Box created successfully!')
            # Do not save the formset here, as it has been saved above
            return redirect(self.get_success_url())

        return self.form_invalid(form)
        
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class BoxDetail(DetailView):
    model = Box
    template_name = "products/box_detail.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        box = self.object
        can_add = True if self.request.user == box.asker or Invitation.objects.filter(box=box, invited_farmer=self.request.user).exists() and Invitation.objects.get(box=box, invited_farmer=self.request.user).status == "accepted" else False
        box_items = box.items.all()
        farmers_product = Product.objects.filter(seller=self.request.user)
        farmers_product = farmers_product.exclude(pk__in=box_items.values_list("product__pk", flat=True))
        invitations = Invitation.objects.filter(box=box)
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
        if user.is_staff:
            pending_boxes = Box.objects.filter(status="pending")
            confirmed_boxes = [box for box in pending_boxes if box.is_confirmed()]
            return confirmed_boxes
        else: return None #later Error    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if not user.is_staff:
            boxes = Box.objects.filter(Q(asker=user) | Q(farmers__in=[user]))
            invitations_dict = {}
            for box in boxes:
                if user == box.asker:
                    if box not in invitations_dict:
                        invitations_dict[box] = {"box": box, "invitation": []}
                elif box.farmers.filter(pk=user.pk).exists():
                    invitation = Invitation.objects.get(invited_farmer=user, box=box)
                    if box not in invitations_dict:
                        invitations_dict[box] = {"box": box, "invitation": invitation}

            invitations = list(invitations_dict.values())
            context["invitations"] = invitations
            return context

class PendingDecision(View):
    def post(self, request, *args, **kwargs):
        box_id = self.kwargs.get("pk")
        action = request.POST.get("action")
        user = request.user

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
                pass
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
                    box.farmers.remove(user)
                    box.save()
                    invitation.save() 
                elif action == "confirm":
                    box.confirmed.add(user)
                    box.save()
            except Box.DoesNotExist:
                pass

        return redirect("products:pending")
    
    
class AddProductToBox(UpdateView):
    model = Box
    template_name = "products/box_detail.html"
    fields = []

    def get_success_url(self):
        return reverse_lazy("products:box_detail", kwargs={"pk": self.kwargs.get("pk")})
    
    def post(self, request, *args, **kwargs):
        selected_products_pk = json.loads(request.body).get("products")
        selected_products = Product.objects.filter(pk__in=selected_products_pk)
        box = self.get_object()
        box.products.add(*selected_products)
        box.save()
        return JsonResponse({"status": "success"})
    


"""
    PLANT INFORMATION
"""
class IdentifyDisease(TemplateView):
    template_name = "products/identify_disease.html"

    def post(self, request, *args, **kwargs):
        api_url = "https://plant.id/api/v3/health_assessment?details=local_name,description,treatment"
        api_key = settings.PLANT_ID_API_KEY
        latitude = float(request.POST.get("latitude", 0))
        longitude = float(request.POST.get("longitude", 0))
        similar_images = True
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
        response = requests.post(api_url, data=data, files=files, headers=headers)
        # Process the response
        if response.status_code == 201:
            result = response.json()
            return render(request, "products/disease_info.html", {"data": result})
        else:
            result = "Error"
            return render(request, "products/disease_info.html", {"message": result})

        
class DiseaseInfo(TemplateView):
    template_name = "products/disease_info.html"

    def get(self, request, *args, **kwargs):
        data_json = request.GET.get("data", "{}")
        data = json.loads(data_json)
        return render(request, self.template_name, {"data": data})
    
"""
    Serializer View
"""   
from rest_framework import viewsets
from .serializers import ProductSerializer, BoxSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer    

class BoxViewSet(viewsets.ModelViewSet):
    queryset = Box.objects.all()
    serializer_class = BoxSerializer  
    

    