from django.db import models
from django.contrib import auth
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField
import requests

# Source: https://www.geoapify.com/tutorial/geocoding-python

# Create your models here.
class User(auth.models.AbstractUser):
    username = models.CharField(max_length=50, unique=True)
    is_farmer = models.BooleanField(default=False)
    farm_nr = models.CharField(max_length=200, null=True)
    address = models.CharField(max_length=300, null=True)
    city = models.CharField(max_length=200, null=True)
    state = models.CharField(max_length=50, null=True)
    zip_code = models.CharField(max_length=20, null=True)
    country = CountryField(null=True)
    phone_number = PhoneNumberField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    profile_pic = models.ImageField(upload_to="pfp/", blank=True, null=True)
    avg_rating = models.DecimalField(max_digits=2, decimal_places=1, default=0)
    bio = models.TextField(blank=True)

    def __str__(self):
        return "@{}".format(self.username)
    
    def translate_address(self, address):
        API_KEY = "dc6022f53f114e3982208865dcc884a4"
        url = f"https://api.geoapify.com/v1/geocode/search?text={address}&apiKey={API_KEY}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            result = data["features"][0]
            return (result["geometry"]["coordinates"][1], result["geometry"]["coordinates"][0])

        else:
            print(f"Request failed: {response.status_code}")
            return None

    def save(self, *args, **kwargs):
        if self.address and self.city and self.state and self.zip_code and self.country:
            address = address = f"{self.address}, {self.city}, {self.state}, {self.zip_code}, {self.country.name}"
            coordinates = self.translate_address(address)
            if coordinates:
                self.latitude, self.longitude = coordinates

        return super().save(*args, **kwargs)