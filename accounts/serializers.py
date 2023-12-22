from rest_framework import serializers
from .models import User

"""
Serializer for converting farmers fields into JSON format
    - model: is the model associated with the farmers
    - fields: the fields to be serialized
"""
class FarmerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("pk", "username", "first_name", "last_name", "email", "address", "avg_rating")