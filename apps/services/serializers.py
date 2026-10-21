from rest_framework import serializers
from .models import *



class ServiceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ('id', 'title', 'slug', 'image', 'category', 'is_active', 'order')


class ServiceDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ('id', 'title', 'slug', 'description', 'image', 'category', 'is_active', 'order')


class PriceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceItem
        fields = ('id', 'category', 'service', 'title', 'description', 'price', 'duration_minutes', 'discount_percent', 'is_active')


class PriceCategorySerializer(serializers.ModelSerializer):
    price = PriceItemSerializer(many=True, read_only=True)

    class Meta:
        model = PriceCategory
        fields = ('id', 'title', 'slug', 'order', 'price')