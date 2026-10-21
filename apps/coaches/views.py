from rest_framework import viewsets
from .models import Coach
from .serializers import CoachListSerializer, CoachDetailSerializer



class CoachViewSet(viewsets.ModelViewSet):
    queryset = Coach.objects.all()
    serializer_class = CoachDetailSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return CoachListSerializer
        
        return super().get_serializer_class()