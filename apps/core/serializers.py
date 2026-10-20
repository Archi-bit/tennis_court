from rest_framework import serializers
from .models import *



class ClubInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubInfo
        fields = '__all__'


class ClubRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubRule
        fields = '__all__'