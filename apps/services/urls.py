from rest_framework.routers import SimpleRouter
from .views import ServiceViewSet, PriceCategoryViewSet, PriceItemViewSet

router = SimpleRouter()

router.register('services', ServiceViewSet, basename='services')
router.register('price-categories', PriceCategoryViewSet, basename='price-category')
router.register('prices', PriceItemViewSet, basename='prices')

urlpatterns = router.urls