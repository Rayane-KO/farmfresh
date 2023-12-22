from rest_framework import serializers
from .models import *

# Source:
#   - BoxSerializer logic: https://stackoverflow.com/questions/60289875/cart-and-cart-item-relations-in-django-rest-framework
#                          https://www.django-rest-framework.org/api-guide/serializers/#modelserializer

"""
Serializer for converting Product, Box and BoxItem fields into JSON format
    - model: is the model associated with the object
    - fields: the fields to be serialized
"""

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ("pk", "name", "categories", "price", "unit", "description", "avg_rating", "available")

class BoxItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoxItem
        fields = ['pk', 'product', 'quantity', 'price']

class BoxSerializer(serializers.ModelSerializer):
    items = BoxItemSerializer(many=True, read_only=True)

    class Meta:
        model = Box
        fields = ['pk', 'name', 'farmers', 'asker', 'description', 'price',
                  'available', 'date', 'status', 'items']

    # override the create method because when creating a box, you need to create box items
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        box = Box.objects.create(**validated_data)
        for item_data in items_data:
            BoxItem.objects.create(box=box, **item_data)
        return box