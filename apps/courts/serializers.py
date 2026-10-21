from rest_framework import serializers
from .models import * 
from apps.news.serializers import GalleryImageSerializer



class CourtTypeSerializer(serializers.ModelSerializer):
    courts_count = serializers.SerializerMethodField()

    class Meta:
        model = CourtType
        fields = '__all__'
        read_only_fields = ('slug', )

    def get_courts_count(self, obj):
        return obj.court_type.count()


class CourtListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Court
        fields = ('id', 'court_number', 'is_active')


class CourtDetailSerializer(serializers.ModelSerializer):
    court_type = CourtTypeSerializer(read_only=True)

    court_type_id = serializers.PrimaryKeyRelatedField(queryset=CourtType.objects.all(), source='court_type', write_only=True)

    gallery_images = GalleryImageSerializer(source='courts', many=True, read_only=True)

    class Meta:
        model = Court
        fields = ('id', 'court_number', 'court_type', 'court_type_id', 'is_active', 'description', 'gallery_images')