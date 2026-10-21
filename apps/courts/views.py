from rest_framework import viewsets
from .models import Court, CourtType
from .serializers import CourtTypeSerializer, CourtListSerializer, CourtDetailSerializer



class CourtTypeViewSet(viewsets.ModelViewSet):
    queryset = CourtType.objects.all()
    serializer_class = CourtTypeSerializer


class CourtViewSet(viewsets.ModelViewSet):
    queryset = Court.objects.all()
    serializer_class = CourtDetailSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return CourtListSerializer

        return super().get_serializer_class()