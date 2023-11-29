from typing import Any
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django import forms
from accounts.models import User


class UserSignUpForm(UserCreationForm):

    user_type = forms.ChoiceField(choices=[
        ("customer", "Customer"),
        ("farmer", "Farmer"),
    ])

    farm_nr = forms.CharField(required=False)

    class Meta:
        fields = ("username", "first_name", "last_name", "email", "password1", "password2", "user_type", "farm_nr")
        model = get_user_model()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  
        self.fields["username"].label = "Username"
        self.fields["email"].label = "Email Adress" 

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_farmer = self.cleaned_data["user_type"] == "farmer"

        if commit:
            user.save()

        return user

    def clean_farm_nr(self):
        farm_nr = self.cleaned_data["farm_nr"]
        user_type = self.cleaned_data["user_type"]

        if user_type == "farmer" and not farm_nr.startswith("FSA"):
            raise forms.ValidationError("The farm-number must start with FSA")
        
        return farm_nr
    
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "bio", "address", "city", "state", "zip_code", "country", "phone_number", "profile_pic")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  
        self.fields["profile_pic"].label = "Choose a profile picture"


