from rest_framework import viewsets

from .models import Tournament
from .serializers import TournamentListSerializer, TournamentDetailSerializer



class TournamentViewSet(viewsets.ModelViewSet):
    queryset = Tournament.objects.all()
    serializer_class = TournamentDetailSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return TournamentListSerializer

        return super().get_serializer_class()