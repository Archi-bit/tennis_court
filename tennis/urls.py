from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import *

router = SimpleRouter()
router.register('rules', ClubRuleViewSet, basename='rules')
router.register('courts', CourtViewSet, basename='court')
router.register('court-types', CourtTypeViewSet, basename='court-types')
router.register('coaches', CoachViewSet, basename='coach')
router.register('services', ServiceViewSet, basename='services')
router.register('price-categories', PriceCategoryViewSet, basename='price-category')
router.register('prices', PriceItemViewSet, basename='prices')
router.register('news', NewsViewSet, basename='news')
router.register('gallery', GalleryImageViewSet, basename='gallery')
router.register('tournaments', TournamentViewSet, basename='tournaments')

urlpatterns = [
    path('club/', ClubInfoView.as_view(), name='club-info'),
    path('', include(router.urls)),
]
