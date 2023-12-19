from rest_framework import serializers
from .models import User

class FarmerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("pk", "username", "first_name", "last_name", "email", "address", "avg_rating")