from django.db import models
from django.db.models import Avg
from accounts.models import User
from products.models import Product
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError

"""
Review: abstract model with attributes:
    - user: is the user associated with the review
    - rating: is the users rating
    - review: is the users comment
    - date: is the date the review was created
ProductReview: inherits from Review with attributes:
    - product: is the product associated with the review
ProductReview: inherits from Review with attributes:
    - farmer: is the farmer associated with the review
FarmerReply: a farmer can reply to a product or farmer review
    - product_review: review of a product
    - farmer_review = review of a farmer
    - farmer = farmer who replies to a review
    - reply = comment of the reply
    - date = the date the reply was created
"""

# get the average rating of reviews
def calc_avg_rating(reviews):
     avg = reviews.aggregate(Avg("rating"))["rating__avg"]
     return round(avg, 1) if avg is not None else 0
     
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
        # abstract to not be able to create instances of Review
        abstract = True

    def __str__(self):
         return f"{self.user.username} review for "

# update the avg_rating of the correspondend product when saving or deleting a review
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
        
class FarmerReply(models.Model):
     product_review = models.ForeignKey(ProductReview, on_delete=models.CASCADE, related_name="replies", null=True, blank=True)
     farmer_review = models.ForeignKey(FarmerReview, on_delete=models.CASCADE, related_name="replies", null=True, blank=True)
     farmer = models.ForeignKey(User, on_delete=models.CASCADE)
     reply = models.TextField()
     date = models.DateTimeField(auto_now_add=True)

     def __str__(self):
          if self.product_review:
            return f"Reply by {self.farmer.username} on {self.product_review}"
          elif self.farmer_review:
            return f"Reply by {self.farmer.username} on {self.farmer_review}"
        