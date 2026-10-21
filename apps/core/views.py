from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.generics import RetrieveUpdateAPIView
from .models import ClubInfo, ClubRule
from .serializers import ClubInfoSerializer, ClubRuleSerializer



class ClubInfoView(RetrieveUpdateAPIView):
    serializer_class = ClubInfoSerializer

    def get_object(self):
        obj = get_object_or_404(ClubInfo, pk=1)
        self.check_object_permissions(self.request, obj)
        return obj


class ClubRuleViewSet(viewsets.ModelViewSet):
    queryset = ClubRule.objects.all()
    serializer_class = ClubRuleSerializer