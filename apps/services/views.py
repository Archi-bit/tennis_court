from rest_framework import viewsets
from .models import Service, PriceCategory, PriceItem
from .serializers import ServiceListSerializer, ServiceDetailSerializer, PriceItemSerializer, PriceCategorySerializer



class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceDetailSerializer

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