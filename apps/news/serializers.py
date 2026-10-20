from rest_framework import serializers
from .models import *



class NewsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ('id', 'title', 'slug', 'short_description', 'image', 'created_at', 'is_published')
        read_only_fields = ('created_at', )


class NewsDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ('id', 'title', 'slug', 'short_description', 'content', 'image', 'created_at', 'updated_at', 'is_published')
        read_only_fields = ('created_at', 'updated_at')


class GalleryImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GalleryImage
        fields = '__all__'