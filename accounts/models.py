from django.db import models
from django.contrib import auth
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField
import requests

# Source: https://www.geoapify.com/tutorial/geocoding-python

"""
A custom user model that has next attributes:
    username: a unique username for each user
    is_farmer: a boolean field that tells if a user is a farmer or a customer
    farm_nr: a field for the farm number of the farmer (is unique to each farmer and only farmers have one)
    address, city, state, zip_code and country: address of the user
    phone_number: phone number of the user
    latitude, longitude: calculated using the address to pin it on the map
    profile_pic: the user can have a profile picture
    avg_rating: this field is only for the farmers, it's their average rating
    bio: the biography of the user
"""
class User(auth.models.AbstractUser):
    username = models.CharField(max_length=50, unique=True)
    is_farmer = models.BooleanField(default=False)
    farm_nr = models.CharField(max_length=200, null=True, unique=True)
    address = models.CharField(max_length=300, null=True)
    city = models.CharField(max_length=200, null=True)
    state = models.CharField(max_length=50, null=True)
    zip_code = models.CharField(max_length=20, null=True)
    country = CountryField(null=True)
    phone_number = PhoneNumberField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    profile_pic = models.ImageField(upload_to="pfp/", blank=True, null=True, default="pfp/default.jpg")
    avg_rating = models.DecimalField(max_digits=2, decimal_places=1, default=0)
    bio = models.TextField(blank=True)

    def __str__(self):
        return "@{}".format(self.username)
    
    # translate_address takes an address like (147, Grote Veldstraat, Staden, Roeselare 8840)
    # and translates it to latitude and longitude
    def translate_address(self, address):
        # the API-key to access Geoapify API
        API_KEY = "dc6022f53f114e3982208865dcc884a4"
        # then build the API url for the request
        url = f"https://api.geoapify.com/v1/geocode/search?text={address}&apiKey={API_KEY}"
        # send the API request and get the response
        response = requests.get(url)

        # check for successfull status_code (200)
        if response.status_code == 200:
            data = response.json() # parse the JSON data
            result = data["features"][0]
            return (result["geometry"]["coordinates"][1], result["geometry"]["coordinates"][0])

        else:
            print(f"Request failed: {response.status_code}")
            return None

    # use translate_address to get the latitude and longitude
    def save(self, *args, **kwargs):
        if self.address and self.city and self.state and self.zip_code and self.country:
            address = address = f"{self.address}, {self.city}, {self.state}, {self.zip_code}, {self.country.name}"
            coordinates = self.translate_address(address)
            if coordinates:
                self.latitude, self.longitude = coordinates

        return super().save(*args, **kwargs)