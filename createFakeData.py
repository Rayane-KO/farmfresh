import os 
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "farmfresh.settings")

import django 
django.setup() 

from faker import factory,Faker 
from accounts.models import * 
from products.models import * 
from reviews.models import *
from orders.models import *
from model_bakery.recipe import Recipe,foreign_key 
import random


fake = Faker("nl_BE") 
categories = Category.objects.all()

# Source: https://www.educative.io/courses/django-admin-web-developers/populating-the-database-with-fake-data
for k in range(0):
    user=User(
        username=fake.user_name(),
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        email=fake.email(),
        is_farmer=fake.boolean(),
        farm_nr=f"FSA{fake.random_int(min=100, max=10000)}",
        address=fake.street_address(),
        city=fake.city(),
        state=fake.province(),
        phone_number=fake.phone_number(),
        zip_code=fake.postcode(),
        country="Belgium",
        bio=fake.text()
    )
    user.save()

for i in range(20):
    product = random.choice(Product.objects.all())
    user = random.choice(User.objects.filter(is_farmer=False))
    product_review = ProductReview(
        user=user,
        product=product,
        rating=random.randint(1, 5),
        review=fake.text()
    )
    product_review.save()

    farmer = random.choice(User.objects.filter(is_farmer=True))
    farmer_review = FarmerReview(
        user=user,
        farmer=farmer,
        rating=random.randint(1, 5),
        review=fake.text()
    )
    farmer_review.save()
    
    