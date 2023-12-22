from typing import Any
from django.contrib.auth.forms import UserCreationForm
from django import forms
from accounts.models import User


"""
    UserSignUpForm: form for when the user wants to sign up
    UserUpdateForm: form for when a user wants to update their profile
"""

class UserSignUpForm(UserCreationForm):
    # user can either be a farmer or customer
    user_type = forms.ChoiceField(choices=[
        ("customer", "Customer"),
        ("farmer", "Farmer"),
    ])
    # each farmer has a unique farm number (this means that customers can't create a farmer account because they don't have this farm number)
    farm_nr = forms.CharField(required=False)

    class Meta:
        # specify fields to be filled in
        fields = ("username", "first_name", "last_name", "email", "password1", "password2", "user_type", "farm_nr", "address", "city", "state", "zip_code", "country")
        model = User

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  
        self.fields["username"].label = "Username"
        self.fields["email"].label = "Email Address" 
        self.fields["user_type"].label = "Are you a"
        self.fields["farm_nr"].label = "Farm Number"

    def save(self, commit=True):
        user = super().save(commit=False)
        # update the is_farmer attribute
        user.is_farmer = self.cleaned_data["user_type"] == "farmer"
        user.save()
        return user

    # use clean to validate a specific field
    def clean_farm_nr(self):
        # validation for the farm_nr field
        farm_nr = self.cleaned_data["farm_nr"]
        user_type = self.cleaned_data["user_type"]
        # if the use selected farmer he must add his farm number (in this example farm numbers start with FSA)
        if user_type == "farmer" and not farm_nr.startswith("FSA"):
            # if it's not correct raise an error to notify user
            raise forms.ValidationError("The farm-number must start with FSA")
        return farm_nr
    
class UserUpdateForm(forms.ModelForm):
    class Meta:
        fields = ("username", "bio", "address", "city", "state", "zip_code", "country", "phone_number", "profile_pic")
        model = User

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  
        # update the label of profile_pic field
        self.fields["profile_pic"].label = "Select a profile picture"


