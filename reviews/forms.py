from django import forms
from .models import ProductReview, FarmerReview, FarmerReply

"""
    ProductReviewForm: form for when the user wants to create a product review
    FarmerReviewForm: form for when a user wants to create a farmer review
    FarmerReplyForm: form for when the farmer wants to reply to a user review
"""

class ProductReviewForm(forms.ModelForm):
    class Meta:
        model = ProductReview
        # fields to be filled in
        fields = ("rating", "review")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  
        self.fields["rating"].label = "How much would you rate it?"
        self.fields["review"].label = "Why?" 

class FarmerReviewForm(forms.ModelForm):
    class Meta:
        model = FarmerReview
        fields = ("rating", "review")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  
        self.fields["rating"].label = "How much would you rate it?"
        self.fields["review"].label = "Why?" 

class FarmerReplyForm(forms.ModelForm):
    class Meta:
        model = FarmerReply
        fields = ("reply",)