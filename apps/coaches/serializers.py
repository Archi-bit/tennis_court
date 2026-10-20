from rest_framework import serializers
from .models import *



class CoachListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coach
        fields = ('id', 'full_name', 'photo', 'experience', 'specialization', 'is_active', 'order')


class CoachDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coach
        fields = ('id', 'full_name', 'photo', 'short_bio', 'experience', 'specialization', 'is_active', 'order')
