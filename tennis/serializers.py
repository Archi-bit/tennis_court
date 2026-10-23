from rest_framework import serializers

from .models import (
    ClubInfo, ClubRule, CourtType, Court, Coach, Service, PriceCategory,
    PriceItem, News, GalleryImage, Tournament,
)


class ClubInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubInfo
        fields = '__all__'


class ClubRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubRule
        fields = '__all__'


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
        fields = ('id', 'court_number', 'court_type_id', 'is_active')


class CourtDetailSerializer(serializers.ModelSerializer):
    court_type = CourtTypeSerializer(read_only=True)

    court_type_id = serializers.PrimaryKeyRelatedField(queryset=CourtType.objects.all(), source='court_type', write_only=True)

    gallery_images = GalleryImageSerializer(source='courts', many=True, read_only=True)

    class Meta:
        model = Court
        fields = ('id', 'court_number', 'court_type', 'court_type_id', 'is_active', 'description', 'gallery_images')


class CoachListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coach
        fields = ('id', 'full_name', 'photo', 'experience', 'specialization', 'is_active', 'order')


class CoachDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coach
        fields = ('id', 'full_name', 'photo', 'short_bio', 'experience', 'specialization', 'is_active', 'order')


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
    price = serializers.SerializerMethodField()

    class Meta:
        model = PriceCategory
        fields = ('id', 'title', 'slug', 'order', 'price')

    def get_price(self, obj):
        request = self.context.get('request')

        if request and request.user.is_staff:
            prices = obj.price.all()
        else:
            prices = obj.price.filter(is_active=True)

        return PriceItemSerializer(prices, many=True, context=self.context).data


class TournamentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournament
        fields = ('id', 'title', 'slug', 'image', 'start_date', 'end_date', 'status', 'is_published')


class TournamentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournament
        fields = ('id', 'title', 'slug', 'description', 'image', 'start_date', 'end_date', 'status', 'is_published')

    def validate(self, attrs):
        start_date = attrs.get('start_date', getattr(self.instance, 'start_date', None))
        end_date = attrs.get('end_date', getattr(self.instance, 'end_date', None))

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({
                'end_date': 'Дата окончания не может быть раньше даты начала'
            })

        return attrs