from rest_framework import serializers
from .models import * 



class CourtTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourtType
        fields = '__all__'


class CourtListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Court
        fields = ('id', 'court_number', 'is_active')


class CourtDetailSerializer(serializers.ModelSerializer):
    court_type = CourtTypeSerializer(read_only=True)

    class Meta:
        model = Court
        fields = ('id', 'court_number', 'court_type', 'is_active', 'description')