from django.views.generic import CreateView
from .models import ProductReview
from .forms import ProductReviewForm
from django.shortcuts import get_object_or_404
from products.models import Product
from django.urls import reverse_lazy

class CreateProductReview(CreateView):
    form_class = ProductReviewForm
    model = ProductReview
    template_name = "products/product_detail.html"

    def form_valid(self, form):
        product = get_object_or_404(Product, pk=self.kwargs.get("pk"))
        form.instance.user = self.request.user
        form.instance.product = product
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy("products:product_detail", kwargs={"pk": self.kwargs.get("pk")})
    
