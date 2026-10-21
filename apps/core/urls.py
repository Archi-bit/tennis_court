from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import ClubInfoView, ClubRuleViewSet

router = SimpleRouter()
router.register('rules', ClubRuleViewSet, basename='rules')

urlpatterns = [
    path('club', ClubInfoView.as_view(), name='club-info'),
    path('', include(router.urls)),
]
