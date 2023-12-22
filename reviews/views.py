from django.views.generic import CreateView
from .models import ProductReview, FarmerReview, FarmerReply
from .forms import ProductReviewForm, FarmerReviewForm, FarmerReplyForm
from django.shortcuts import get_object_or_404
from products.models import Product
from accounts.models import User
from django.urls import reverse_lazy

"""
Views for handeling review management:
    CreateProductReview: handles the creation of a product review
    CreateFarmerReview: handles the creation of a farmer review
    CreateFarmerReply: handles the creation of a farmer reply
"""

class CreateProductReview(CreateView):
    form_class = ProductReviewForm
    model = ProductReview
    template_name = "products/product_detail.html"

    def form_valid(self, form):
        product = get_object_or_404(Product, pk=self.kwargs.get("pk"))
        # update the info of the review
        form.instance.user = self.request.user
        form.instance.product = product
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy("products:product_detail", kwargs={"pk": self.kwargs.get("pk")})
    
class CreateFarmerReview(CreateView):
    form_class = FarmerReviewForm
    model = FarmerReview
    template_name = "accounts/user_detail.html"

    def form_valid(self, form):
        farmer = get_object_or_404(User, pk=self.kwargs.get("pk"))
        # update the info of the review
        form.instance.user = self.request.user
        form.instance.farmer = farmer
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy("accounts:user_detail", kwargs={"pk": self.kwargs.get("pk")})
    
class CreateFarmerReply(CreateView):
    form_class = FarmerReplyForm
    model = FarmerReply

    def get_template_names(self):
        # get the type of review (product or farmer)
        review_type = self.kwargs.get("type") 
        # take the correct template depending on the review type
        if review_type == "farmer":
            return ["accounts/user_detail.html"]
        else:
            return ["products/product_detail.html"]
    
    def get_success_url(self):
        review_type = self.kwargs.get("type") 
        # when the review was successfully created redirect the user to the correct page
        if review_type == "farmer":
            farmer_review = get_object_or_404(FarmerReview, pk=self.kwargs.get("pk"))
            return reverse_lazy("accounts:user_detail", kwargs={"pk": farmer_review.farmer.pk})
        elif review_type == "product":
            product_review = get_object_or_404(ProductReview, pk=self.kwargs.get("pk"))
            return reverse_lazy("products:product_detail", kwargs={"pk": product_review.product.pk})
        else:
            raise NotImplementedError("Invalid review type")

    def form_valid(self, form):
        review_type = self.kwargs.get("type") 
        # update the information of the reply
        if review_type == "farmer":
            farmer_review = get_object_or_404(FarmerReview, pk=self.kwargs.get("pk"))
            form.instance.farmer_review = farmer_review
        elif review_type == "product":
            product_review = get_object_or_404(ProductReview, pk=self.kwargs.get("pk"))
            form.instance.product_review = product_review
        else:
            raise NotImplementedError("Invalid review type")
        form.instance.farmer = self.request.user
        return super().form_valid(form)
    
    
