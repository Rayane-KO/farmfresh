from django import forms
from .models import ProductReview, FarmerReview, FarmerReply

class ProductReviewForm(forms.ModelForm):
    class Meta:
        model = ProductReview
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