from django.db import models
from django.db.models import Avg
from accounts.models import User
from products.models import Product
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError

def calc_avg_rating(reviews):
     avg = reviews.aggregate(Avg("rating"))["rating__avg"]
     return round(avg, 1) if avg is not None else 0
     

# Create your models here.
class Review(models.Model):

    RATING=[
        (0, "0"),
        (1, "1"),
        (2, "2"),
        (3, "3"),
        (4, "4"),
        (5, "5"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0, choices=RATING, validators=[MinValueValidator(0), MaxValueValidator(5)])
    review = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    def __str__(self):
         return f"{self.user.username} review for "

class ProductReview(Review):
        product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="review_set")

        def save(self, *args, **kwargs):
            super().save(*args, **kwargs)
            self.product.avg_rating = calc_avg_rating(self.product.review_set)
            self.product.save()

        def delete(self, *args, **kwargs):
            super().delete(*args, **kwargs)
            self.product.avg_rating = calc_avg_rating(self.product.review_set)
            self.product.save()

        def __str__(self):
             return super().__str__() + self.product.name

class FarmerReview(Review):
        farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="farmer_reviews")

        def clean(self):
             if self.farmer and not self.farmer.is_farmer:
                  raise ValidationError("User must be a farmer!")
             return super().clean()

        def save(self, *args, **kwargs):
            super().save(*args, **kwargs)
            self.farmer.avg_rating = calc_avg_rating(self.farmer.farmer_reviews)
            self.farmer.save()

        def delete(self, *args, **kwargs):
            super().delete(*args, **kwargs)
            self.farmer.avg_rating = calc_avg_rating(self.farmer.farmer_reviews)
            self.farmer.save()

        def __str__(self):
             return super().__str__() + self.farmer.username
        