from rest_framework import serializers
from .models import *



class TournamentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournament
        fields = ('id', 'title', 'slug', 'image', 'start_date', 'end_date', 'status', 'is_published')


class TournamentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournament
        fields = ('id', 'title', 'slug', 'description', 'image', 'start_date', 'end_date', 'status', 'is_published')
