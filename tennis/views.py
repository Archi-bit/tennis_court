from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.generics import RetrieveUpdateAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import (ClubInfo, ClubRule, CourtType, Court, Coach, Service, PriceCategory, PriceItem, News, GalleryImage, Tournament)
from .serializers import (
    ClubInfoSerializer, ClubRuleSerializer, CourtTypeSerializer, CourtListSerializer, CourtDetailSerializer, CoachListSerializer,
    CoachDetailSerializer, ServiceListSerializer, ServiceDetailSerializer, PriceCategorySerializer, PriceItemSerializer, NewsListSerializer,
    NewsDetailSerializer, GalleryImageSerializer, TournamentListSerializer, TournamentDetailSerializer,
)
from .pagination import SixPerPagePagination



class ClubInfoView(RetrieveUpdateAPIView):
    serializer_class = ClubInfoSerializer

    def get_object(self):
        obj = get_object_or_404(ClubInfo, pk=1)
        self.check_object_permissions(self.request, obj)
        return obj


class ClubRuleViewSet(viewsets.ModelViewSet):
    queryset = ClubRule.objects.all()
    serializer_class = ClubRuleSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return ClubRule.objects.all()
        
        return ClubRule.objects.filter(is_active=True) 


class CourtTypeViewSet(viewsets.ModelViewSet):
    queryset = CourtType.objects.all()
    serializer_class = CourtTypeSerializer


class CourtViewSet(viewsets.ModelViewSet):
    queryset = Court.objects.all()
    serializer_class = CourtDetailSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['court_type']

    def get_queryset(self):
        if self.request.user.is_staff:
            return Court.objects.all()

        return Court.active_objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return CourtListSerializer

        return super().get_serializer_class()


class CoachViewSet(viewsets.ModelViewSet):
    queryset = Coach.objects.all()
    serializer_class = CoachDetailSerializer
    filter_backends = [SearchFilter]
    search_fields = ['full_name']

    def get_queryset(self):
        if self.request.user.is_staff:
            return Coach.objects.all()

        return Coach.active_objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return CoachListSerializer
        
        return super().get_serializer_class()


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceDetailSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category']

    def get_queryset(self):
        if self.request.user.is_staff:
            return Service.objects.all()

        return Service.objects.filter(is_active=True)

    def get_serializer_class(self):
        if self.action == 'list':
            return ServiceListSerializer

        return super().get_serializer_class()


class PriceCategoryViewSet(viewsets.ModelViewSet):
    queryset = PriceCategory.objects.all()
    serializer_class = PriceCategorySerializer


class PriceItemViewSet(viewsets.ModelViewSet):
    queryset = PriceItem.objects.all()
    serializer_class = PriceItemSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category']

    def get_queryset(self):
        if self.request.user.is_staff:
            return PriceItem.objects.all()

        return PriceItem.active_objects.all()


class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsDetailSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['title']
    ordering_fields = ['created_at']
    ordering = ['-created_at', '-id']
    pagination_class = SixPerPagePagination

    def get_queryset(self):
        if self.request.user.is_staff:
            return News.objects.all()

        return News.published_objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return NewsListSerializer
        
        return super().get_serializer_class()


class GalleryImageViewSet(viewsets.ModelViewSet):
    queryset = GalleryImage.objects.all()
    serializer_class = GalleryImageSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['category']
    ordering_fields = ['order']
    ordering = ['order', 'id']


class TournamentViewSet(viewsets.ModelViewSet):
    queryset = Tournament.objects.all()
    serializer_class = TournamentDetailSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']
    pagination_class = SixPerPagePagination

    def get_queryset(self):
        if self.request.user.is_staff:
            return Tournament.objects.all()

        return Tournament.published_objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return TournamentListSerializer

        return super().get_serializer_class()
